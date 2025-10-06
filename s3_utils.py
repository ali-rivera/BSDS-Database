#helper functions for AWS S3 upload

import boto3
import os
from pymongo import MongoClient
from dotenv import load_dotenv
from botocore.client import Config


#load AWS credentials
load_dotenv()

def get_bucket_name():
    b = (
        os.getenv("AWS_S3_BUCKET_NAME")
    )
    if not b:
        raise RuntimeError("No S3 bucket env set")
    return b

#initialize boto3 s3 client
def get_s3_client():
    endpoint = os.getenv("AWS_S3_ENDPOINT_URL") 
    kwargs = {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
        "region_name": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
    }
    if endpoint:
        kwargs["endpoint_url"] = endpoint
        kwargs["config"] = Config(signature_version="s3v4", s3={"addressing_style": "path"})
    else:
        # AWS: virtual-hosted style
        kwargs["config"] = Config(s3={"addressing_style": "virtual"})
    return boto3.client("s3", **kwargs)

def upload_file_to_s3(file_path: str, s3_key: str) -> str | None:    
    """
    Uploads a file to S3 and returns the public file URL.
    file_path: local file path (e.g., 'datasets/bank.csv')
    s3_key: desired path/key in S3 (e.g., 'datasets/bank.csv')
    """
    s3 = get_s3_client()
    bucket = get_bucket_name()

    try:
        s3.upload_file(
            Filename=file_path,
            Bucket=bucket,
            Key=s3_key,
        )
        endpoint = os.getenv("AWS_S3_ENDPOINT_URL")
        if endpoint:
            return f"{endpoint.rstrip('/')}/{bucket}/{s3_key}"
        return s3.generate_presigned_url(
            "get_object", Params={"Bucket": bucket, "Key": s3_key}, ExpiresIn=3600
        )
    except Exception as e:
        print(f"Upload failed: Failed to upload {file_path} to {bucket}/{s3_key}: {e}")
        return None
    

def cleanup_orphaned_entries():
    """
    Deletes a file from S3.
    s3_key: path/key in S3 (e.g., 'datasets/bank.csv')
    """
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
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
