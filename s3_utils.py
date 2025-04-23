#helper functions for AWS S3 upload

def upload_file_to_s3(file_path, s3_key):
    import boto3
    import os
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
            # ExtraArgs={"ACL": "public-read"}  # Makes it viewable by URL
        )
        url = f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
        return url
    except Exception as e:
        print("Upload failed:", e)
        return None