import boto3
import json
import os
import faiss as faiss
import pickle
import numpy as np
import io
import traceback

class RAGPipeline:
    def __init__(self):
        self.region = os.getenv('REGION', 'us-east-1')
        self.s3_bucket = os.getenv('S3_BUCKET', '')
        self.index_key = os.getenv('S3_FAISS_FILE', '')
        self.metadata_key = os.getenv('S3_METADATA_FILE', '')
        self.embedding_model_id = os.getenv('TITAN_EMBEDDING_MODEL_ID', '')
        self.claude_model_id = os.getenv('CLAUDE_3_SONNET_MODEL_ID', '')

        self.s3 = boto3.client('s3', region_name=self.region)
        self.bedrock = boto3.client('bedrock-runtime', region_name=self.region)

        self.index = self.load_faiss_index()
        self.metadata = self.load_metadata()

    def load_faiss_index(self):
        print(f"Trying to load FAISS index from S3 bucket: '{self.s3_bucket}', key: '{self.index_key}'...")
        try:
            obj = self.s3.get_object(Bucket=self.s3_bucket, Key=self.index_key)
            faiss_bytes = obj['Body'].read()
            print(f"Downloaded {len(faiss_bytes)} bytes from S3 for FAISS index.")
            
            # Write bytes to a temporary file
            temp_faiss_file = '/tmp/index.faiss'
            with open(temp_faiss_file, 'wb') as f:
                f.write(faiss_bytes)
            
            # Load FAISS index from file
            index = faiss.read_index(temp_faiss_file)
            print("FAISS index loaded successfully.")
            return index
        except Exception as e:
            print(f"Error loading FAISS index: {e}")
            raise RuntimeError("Failed to load FAISS index from S3.") from e

    def load_metadata(self):
        print("Downloading metadata from S3...")
        try:
            obj = self.s3.get_object(Bucket=self.s3_bucket, Key=self.metadata_key)
            metadata_bytes = obj['Body'].read()
            metadata = pickle.loads(metadata_bytes)
            print("Metadata loaded.")
            return metadata
        except Exception as e:
            print(f"Error loading metadata: {e}")
            raise RuntimeError("Failed to load metadata from S3.") from e

    def get_embedding(self, text):
        body = {"inputText": text}
        response = self.bedrock.invoke_model(
            body=json.dumps(body),
            modelId=self.embedding_model_id,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response['body'].read())
        return np.array(response_body['embedding'], dtype=np.float32)

    def search_faiss(self, embedding, k=5):
        print("Searching FAISS index...")
        distances, indices = self.index.search(np.array([embedding]), k)
        results = [self.metadata[i] for i in indices[0] if i != -1]
        print(f"Found {len(results)} relevant results.")
        return results

    def generate_answer(self, context, question):
        messages = [
            {
                "role": "user",
                "content": f"""
You are a financial assistant. Only use the provided data context if it is relevant to the user's question.

If the user greets you or says something casual like "hi", "hello", or "thank you", respond in a natural, conversational way — without referencing the financial data.

If the user asks a question related to margin calls, collateral, thresholds, volatility, asset, haricut, balance, or financial forecasting, analyze the question using the provided data context.

Context:
{context}

Question:
{question}

Make sure you provide specific numerical values if possible.
"""
            }
        ]

        body = {
            "messages": messages,
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "temperature": 0.3,
            "top_p": 0.9
        }

        response = self.bedrock.invoke_model(
            body=json.dumps(body),
            modelId=self.claude_model_id,
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response['body'].read())
        if 'content' in response_body and isinstance(response_body['content'], list):
            texts = [item.get('text', '') for item in response_body['content'] if item.get('type') == 'text']
            return "\n\n".join(texts) if texts else "Sorry, I could not generate an answer."
        else:
            return "Sorry, I could not generate an answer."

    def ask(self, question, k=5):
        embedding = self.get_embedding(question)
        results = self.search_faiss(embedding, k)

        if not results:
            return "No relevant data found for your question."

        context = "\n\n---\n\n".join([json.dumps(doc, indent=2) for doc in results])
        return self.generate_answer(context, question)

def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    rag = RAGPipeline()
    try:
        question = None

        if event.get('queryStringParameters'):
            question = event['queryStringParameters'].get('question')
            print(f"Extracted question from queryStringParameters: {question}")
        elif event.get('body'):
            try:
                body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
                question = body.get('question')
                print(f"Extracted question from body: {question}")
            except Exception as e:
                print(f"Failed to parse body: {e}")
                question = None
        elif 'question' in event:
            question = event.get('question')
            print(f"Extracted question from root event: {question}")

        if not question:
            print("Missing 'question' parameter in the request.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing question parameter'}),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }

        print(f"DEBUG Received question: {question}")

        answer = rag.ask(question)
        
        print("DEBUG Answer generated successfully.")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'answer': answer}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }

    except Exception as e:
        print(f"ERROR occurred: {e}")
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }