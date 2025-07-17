#helper functions for AWS S3 upload

import boto3
import os
from pymongo import MongoClient
from dotenv import load_dotenv

#load AWS credentials
load_dotenv()

#initialize boto3 s3 client
s3= boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION")
)

def upload_file_to_s3(file_path, s3_key):
    
    """
    Uploads a file to S3 and returns the public file URL.
    file_path: local file path (e.g., 'datasets/bank.csv')
    s3_key: desired path/key in S3 (e.g., 'datasets/bank.csv')
    """
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")

    try:
        s3.upload_file(
            Filename=file_path,
            Bucket=bucket_name,
            Key=s3_key,
        )
        url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        print("Upload failed:", e)
        return None
    

def cleanup_orphaned_entries():
    """
    Deletes a file from S3.
    s3_key: path/key in S3 (e.g., 'datasets/bank.csv')
    """
    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME")
    mongo_user = os.getenv("MONGO_INITDB_ROOT_USERNAME")
    mongo_pass = os.getenv("MONGO_INITDB_ROOT_PASSWORD")
    mongo_db = os.getenv("MONGO_INITDB_DATABASE")
    mongo_collection = "dataset" 
    mongo_host = "localhost"
    mongo_port = 27017

    #connecting to Mongo
    mongo_uri = f"mongodb://{mongo_user}:{mongo_pass}@{mongo_host}:{mongo_port}/?authSource=admin"
    client = MongoClient(mongo_uri)
    db = client[mongo_db]
    collection = db[mongo_collection]
    #getting S3 file list
    print("Fetching file list from S3...")
    s3_objects = s3.list_objects_v2(Bucket=bucket_name)
    s3_keys = set()
    if "Contents" in s3_objects:
        s3_keys = {obj["Key"] for obj in s3_objects["Contents"]}

    #getting Mongo documents
    print("Scanning MongoDB entries...")
    db_entries = list(collection.find({}))
    deleted_count = 0

    for entry in db_entries:
        file_url = entry.get("file_url")
        if not file_url:
            continue
        try:
            s3_key = file_url.split(".com/")[1]
        except IndexError:
            continue  

        if s3_key not in s3_keys:
            print(f"Deleting orphaned entry: {file_url}")
            collection.delete_one({"_id": entry["_id"]})
            deleted_count += 1

    print(f"Cleanup complete. {deleted_count} orphaned MongoDB entries removed.")
