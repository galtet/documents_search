import requests
import json

endpoint = 'http://127.0.0.1:5004/document'

data = json.loads(requests.get('http://intezer-documents-store.westeurope.cloudapp.azure.com/documents').text)
for doc in data['documents']:
    print(requests.post(endpoint, json = doc))


