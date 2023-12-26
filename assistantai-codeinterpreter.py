
# export OPENAI_API_KEY={your key}

from openai import OpenAI, Image
import time
from io import BytesIO
from google.cloud import bigquery
from PIL import Image

# this part optional
# prerequisite is having a GCP account, authenticate by running gcloud auth application-default login
# we use data from the public BigQuery dataset about Austin crime incidents and save it to a csv file
# alternatively, you can upload your own data to the csv file and use it in the code interpreter

project = "my-gcp-project"  # your Google Cloud Platform Project ID 
location = 'US' 
client = bigquery.Client(project=project, location=location)

# query data
query = """
SELECT * FROM `bigquery-public-data.austin_crime.crime`  
"""
# Create a BigQuery job
job = client.query(query)

df = job.to_dataframe()
df.to_csv("df.csv")

client = OpenAI()

file = client.files.create(
  file=open("df.csv", "rb"),
  purpose='assistants'
)

assistant = client.beta.assistants.create(
    name="Data Analyses Tutor",
    instructions="You are my personal data analyses tutor. You will help me analyze data and derive insights from it. Show me the code of your analyses.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-1106-preview",
    file_ids=[file.id]
)

thread = client.beta.threads.create()

print(thread.id)

 # example prompt: Attached is a dataset concerning crime incidents in Austin. Please share any interesting insights you derive from this data. Plot me the output

while True:
  user_input=input("Type your request to generate another response or 'exit' to end: ")
  if user_input.lower() == 'exit':
    break
  else:
    message = client.beta.threads.messages.create(thread_id=thread.id, role="user", content=user_input)
    run = client.beta.threads.runs.create(
      thread_id=thread.id,
      assistant_id=assistant.id,
      instructions="")
    print(run)
  while run.status != "completed":
    run = client.beta.threads.runs.retrieve(
      thread_id=thread.id,
      run_id=run.id
    )
    time.sleep(3)
    print(run.status)
  # uncomment if you are interested in the actual code executed in each of the steps
  '''  
  run_steps = client.beta.threads.runs.steps.list(
    thread_id=thread.id,
    run_id=run.id
  )
  print(run_steps)
  '''
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  for message in messages.data:
    if message.run_id != run.id:
      continue
    if message.content[0].type == "text":
      print(message.content[0].text.value)
    elif message.content[0].type == "image_file":
      response_file = client.files.with_raw_response.content(message.content[0].image_file.file_id)
      bytes_io=BytesIO(response_file.content)
      image = Image.open(bytes_io)
      if image.mode == 'RGBA':
        image = image.convert('RGB')
      image.save("output_image.jpg")


