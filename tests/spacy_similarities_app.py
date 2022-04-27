import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_text
import spacy

from flask import Flask, request
from flask_restful import Resource, Api, reqparse
import logging

from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)
api = Api(app)

@app.route('/')
def testing():
    return 'testing app'
    

app.logger.info('LOADING SPACY MODEL')
nlp = spacy.load('en_core_web_sm')
app.logger.info('LOADING USEM')
module_url = 'https://tfhub.dev/google/universal-sentence-encoder-multilingual-qa/3'

model = hub.load(module_url)
def embed(input):
    return model(input)

app.logger.info('READY APP')



parser_answer = reqparse.RequestParser()
parser_answer.add_argument('sentences')

def sentences_similarity(sentences, mode='usem'):

    similarities = []
    
    if mode == 'usem':
        embeding = embed(sentences)
        corr = np.inner(embeding, embeding)
        for n,s in enumerate(corr):
            for q in s[n+1:]:
        
                app.logger.info('corr {}'.format(float(q)))
                similarities.append(float(q))
    if mode == 'spacy':
        for n,s in enumerate(sentences):
            for q in sentences[n+1:]:
                token_s = nlp(s)
                token_q = nlp(q)
                simil = token_s.similarity(token_q) 
                app.logger.info('simil {}'.format(float(simil)))
                similarities.append(float(simil))
        
    return {'error': False, 'similarity': similarities}

class SimilarityTF(Resource):
    def get(self):
        return {"error": True, "message": 'not_implemented'}

    def post(self):

        app.logger.info('SIMILARITY {}'.format('POST CALLED'))

        json_sentences = request.get_json(force=True)
        
        try:
            sentences = json_sentences['sentences']
            
            if len(sentences) < 1 and isinstance(sentences, list):
                return {'error': True, 'message': 'NOT_ENOUGH_SENTENCES'}
            error = sentences_similarity(sentences)
            
            if error['error'] == False:
                
                return {'error': False, 'similarity': error['similarity'] }
            else:
                return error

        except Exception as e:
            app.logger.info('SIMILARITY ERROR {} {}'.format('POST PARSER', e))
            return {'error': True, 'message': 'ERROR_PARSER'}
     
class SimilaritySP(Resource):
    def get(self):
        return {"error": True, "message": 'not_implemented'}

    def post(self):

        app.logger.info('SIMILARITY {}'.format('POST CALLED'))

        json_sentences = request.get_json(force=True)
        
        try:
            sentences = json_sentences['sentences']
            
            if len(sentences) < 1 and isinstance(sentences, list):
                return {'error': True, 'message': 'NOT_ENOUGH_SENTENCES'}
            error = sentences_similarity(sentences, mode='spacy')
            
            if error['error'] == False:
                
                return {'error': False, 'similarity': error['similarity'] }
            else:
                return error

        except Exception as e:
            app.logger.info('SIMILARITY ERROR {} {}'.format('POST PARSER', e))
            return {'error': True, 'message': 'ERROR_PARSER'}

        
'''
curl -d '{"sentences": ["hello world", "hello world"]}' -H 'Content-Type: application/json' -X POST localhost:8000/get_similarity/
'''
api.add_resource(SimilarityTF, '/get_similarity_tf/')
api.add_resource(SimilaritySP, '/get_similarity_sp/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
