#export OPENAI_API_KEY={your key}

from google.cloud import bigquery
from google_auth_oauthlib import flow

import json
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from json import JSONDecodeError
from typing import List, Union
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
)
from langchain_core.agents import AgentAction, AgentActionMessageLog, AgentFinish
from codeinterpreterapi import CodeInterpreterSession, settings, File


# this part optional 
# we download data from the public BigQuery dataset about Austin crime incidents and save it to a csv file
# alternatively, you can upload your own data to the csv file and use it in the code interpreter

project = "my-gcp-project" # your Google Cloud Platform Project ID 
location = 'US' # Location inserted based on the query results selected to explore
client = bigquery.Client(project=project, location=location)

# query data
query = """
SELECT * FROM `bigquery-public-data.austin_crime.crime`  
"""
# Create a BigQuery job
job = client.query(query)

df = job.to_dataframe()
df.to_csv("df.csv")


# monkeypatched method which fixes the problem with json.loads with unescaped newlines \n -> \\n
# original: https://api.python.langchain.com/en/latest/_modules/langchain/agents/output_parsers/openai_functions.html
def my_parse_ai_message(message: BaseMessage) -> Union[AgentAction, AgentFinish]:
    """Parse an AI message. Add json.dumps before doing json.loads to fix escaping errors"""
    if not isinstance(message, AIMessage):
        raise TypeError(f"Expected an AI message got {type(message)}")

    function_call = message.additional_kwargs.get("function_call", {})

    if function_call:
        function_name = function_call["name"]
        try:
            if len(function_call["arguments"].strip()) == 0:
                # OpenAI returns an empty string for functions containing no args
                _tool_input = {}
            else:
                # otherwise it returns a json object
                _tool_input = json.dumps(function_call["arguments"])  # This line was added to the original function
                _tool_input = json.loads(_tool_input)
        except JSONDecodeError:
            raise OutputParserException(
                f"Could not parse tool input: {function_call} because "
                f"the `arguments` is not valid JSON."
            )

        # HACK HACK HACK:
        # The code that encodes tool input into Open AI uses a special variable
        # name called `__arg1` to handle old style tools that do not expose a
        # schema and expect a single string argument as an input.
        # We unpack the argument here if it exists.
        # Open AI does not support passing in a JSON array as an argument.
        if "__arg1" in _tool_input:
            tool_input = _tool_input["__arg1"]
        else:
            tool_input = _tool_input

        content_msg = f"responded: {message.content}\n" if message.content else "\n"
        log = f"\nInvoking: `{function_name}` with `{tool_input}`\n{content_msg}\n"
        return AgentActionMessageLog(
            tool=function_name,
            tool_input=tool_input,
            log=log,
            message_log=[message],
        )

    return AgentFinish(
        return_values={"output": message.content}, log=str(message.content)
    )

OpenAIFunctionsAgentOutputParser._parse_ai_message = my_parse_ai_message

with CodeInterpreterSession(verbose=True) as session:
    user_request = """
      Attached is a dataset concerning crime incidents in Austin. Please share any interesting insights you derive from this data.          
     """
    while True:
        files = [
            # attach files to the request
            File.from_path("df.csv"),
        ]

        # generate the response
        response = session.generate_response(
            user_request, files=files
        )

        # output to the user
        print("AI: ", response.content)
        for file in response.files:
            # iterate over the files (display if image)
            file.show_image()

        # Wait for user input to continue or break the loop
        cont = input("Type your request to generate another response or 'exit' to end: ")
        if cont.lower() == 'exit':
            break
        else:
            user_request = cont

