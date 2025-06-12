import pandas as pd
import faiss
import boto3
import json
import os
import numpy as np
from dotenv import load_dotenv
import pickle

# Load .env variables
load_dotenv()

region = os.getenv('REGION')
s3_bucket = os.getenv('S3_BUCKET')
s3_faiss_file = os.getenv('S3_FAISS_FILE')
s3_metadata_file = os.getenv('S3_METADATA_FILE')

bedrock = boto3.client('bedrock-runtime', region_name=region)
s3 = boto3.client('s3', region_name=region)

def get_embedding(text):
    body = {"inputText": text}
    response = bedrock.invoke_model(
        body=json.dumps(body),
        modelId=os.getenv('TITAN_EMBEDDING_MODEL_ID'),
        accept='application/json',
        contentType='application/json'
    )
    response_body = json.loads(response['body'].read())
    return response_body['embedding']

def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    print(f"JSON loaded successfully with {len(df)} records.")
    return df

def save_faiss_index(index, metadata):
    faiss.write_index(index, "index.faiss")
    with open("metadata.pkl", "wb") as f:
        pickle.dump(metadata, f)
    # Upload to S3
    s3.upload_file("index.faiss", s3_bucket, s3_faiss_file)
    s3.upload_file("metadata.pkl", s3_bucket, s3_metadata_file)
    print(f"FAISS index and metadata uploaded to S3 bucket {s3_bucket}")

def main():
    df = load_json('collateral_data.json')

    dimension = 1024  # Titan Embedding V2 output size
    index = faiss.IndexFlatL2(dimension)

    vectors = []
    metadata = []

    for idx, row in df.iterrows():
        # Text used for embedding generation
        text = (
            f"CalculationDate: {row['CalculationDate']}, Client: {row['Client']}, MTM: {row['MTM']:.2f}, "
            f"CollateralBalance: {row['CollateralBalance']:.2f}, HeldNominal: {row['HeldNominal']:.2f}, "
            f"TotalCollateralMartketValue: {row['TotalCollateralMartketValue']:.2f}, ISIN: {row['ISIN']}, "
            f"AssetName: {row['AssetName']}, Price: {row['Price']}, Haricut: {row['Haricut']}, "
            f"CounterpartyName: {row['CounterpartyName']}, PrincipalName: {row['PrincipalName']}, "
            f"Threshold: {row['Threshold']}, Volatility: {row['Volatility']}, Currency: {row['Currency']}, "
            f"InterestRate: {row['InterestRate']}, FxRate: {row['FxRate']}, MTA: {row['MTA']}, "
            f"MarginCallAmount: {row['MarginCallAmount']:.2f}, "
            f"CountryOfOrigin: {row['CountryOfOrigin']}, Sector: {row['Sector']}, "
            f"ClientResponseTime: {row['ClientResponseTime']}, PaymentAmountDirection: {row['PaymentAmountDirection']}, "
            f"MarginCallMade: {row['MarginCallMade']}"
        )
        embedding = get_embedding(text)
        if embedding:
            vectors.append(embedding)
            metadata.append(row.to_dict())

    vectors_np = np.array(vectors).astype('float32')
    index.add(vectors_np)

    save_faiss_index(index, metadata)

if __name__ == "__main__":
    main()