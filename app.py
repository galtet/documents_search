from flask import Flask, request
from flasgger import Swagger, swag_from
from redis import Redis
import hashlib
import json
import re

open_api_dict_search = {
   "parameters": [
     {
       "in": "query",
       "name": "words",
       "required": True,
       "description": "list of words",
       "schema": {
         "type": "string",
         "example": "This is my house"
       }
     },
    {
       "in": "query",
       "name": "case_sensitive",
       "required": False,
       "description": "case sensitive flag",
       "schema": {
         "type": "boolean",
         "example": "true"
       }
     }
   ],
   "responses": {
     "200": {
       "description": "the list of documents with the words indices and score"
     }
   }
}

open_api_dict_document = {
   "parameters": [
     {
       "in": "body",
       "name": "body",
       "required": True,
       "description": "the content of the document",
       "schema": {
           "id": "Document",
           "required": ["author", "content", "author"]
       },
       "properties": {
            "author": {
                "type": "string",
                "description": "the author",
                "default": "AUTHOR",
                "required": True
            },
            "title": {
                "type": "string",
                "description": "the title",
                "default": "TITLE",
                "required": True

            },
            "content": {
                "type": "string",
                "description": "the content of the document",
                "default": "DOCUMENT",
                "required": True
            }
        }
     }
   ],
   "responses": {
     "200": {
       "description": "Return OK"
     }
   }
}

app = Flask(__name__)
swagger = Swagger(app)

redis = Redis(host='redis', port=6379, decode_responses=True)

excluded_words = ["a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if", "in", "into", "is", "it", "no", "not", "of", "on", "or", "such", "that,the", "their", "then", "there", "these", "they", "this", "to", "was", "will", "with"]

@app.route('/document', methods=['POST'])
@swag_from(open_api_dict_document)
def index_document():
    req_data = request.get_json(force=True)
    content = req_data['content']

    # get words indices
    word_indices = {}
    words = re.findall(r'\w+', content) # extracting the words from the content
    for idx, word in enumerate(words):
        if word not in excluded_words and len(word) > 2:
            word_indices[word] = word_indices.get(word, [])
            word_indices[word].append(idx)

    # set a doc id 
    doc_id = hashlib.md5(content.encode()).hexdigest()
    is_new_doc = redis.hsetnx("documents", doc_id, content)

    # insert the words indices to redis by document id if its a new doc
    if is_new_doc:
        for word, indices in word_indices.items():
            redis.hset(f"{word.upper()}:{word}", doc_id, json.dumps(indices))
        
    return "OK"

# example: curl http://localhost:5004/search?words=father%20mother
@app.route('/search', methods=['GET'])
@swag_from(open_api_dict_search)
def get_documents_by_word():
    case_sensitive = not request.args.get('case_sensitive') == "false"
    try:
      words = set(request.args.get('words').split())
    except Exception:
      return json.dumps([]), 500

    words = filter(lambda word: len(word) > 2 and word not in excluded_words, words)
    if case_sensitive:
        word_keys = [ f"{word.upper()}:{word}" for word in words ]
    else:
        word_keys = sum([ redis.keys(f"{word.upper()}:*") for word in words ], [])
    
    doc_meta_data = {}
    for word_p in word_keys:
        for doc, indices in redis.hgetall(word_p).items():
            indices_arr = json.loads(indices)
            doc_meta_data[doc] = doc_meta_data.get(doc) or {"words": {}, "score": 0}
            doc_meta_data[doc]["score"] += len(indices_arr)
            doc_meta_data[doc]["words"][word_p] = indices_arr
    
    res = [{ "sentence": redis.hget('documents', doc_id), "score": info["score"], "words": info["words"] } for doc_id, info in doc_meta_data.items()]

    return json.dumps(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
