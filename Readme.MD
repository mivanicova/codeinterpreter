The file assistantai-codeinterpreter.py contains sample code to invoke the [Assistant  API](https://platform.openai.com/docs/assistants/overview ) for data analysis purposes.

The file codeinterpreter-api.py contains sample code to invoke the [Codeinterpreter API](https://github.com/shroominic/codeinterpreter-api) for data analysis purposes.


1. pip install -r requirements.txt
1. export OPENAI_API_KEY={your key obtained from https://openai.com}
1. authenticate with your GCP account to access BigQuery sample (public Austin crime incidents dataset): gcloud auth application-default login 
1. replace my-gcp-project, with your GCP project

You can skip the BigQuery part, by commenting out the code which connects to GCP. Alternatively you can prepare your data in the file "df.csv".
