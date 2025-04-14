import boto3

def get_s3_client(aws_key, aws_secret, region='us-east-1'):
    return boto3.client(
        's3',
        aws_access_key_id=aws_key,
        aws_secret_access_key=aws_secret,
        region_name=region
    )

def list_s3_files(bucket, prefix, client):
    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'] for obj in response.get('Contents', [])]

def download_s3_file(bucket, key, client):
    response = client.get_object(Bucket=bucket, Key=key)
    return response['Body'].read()

def delete_s3_file(bucket, key, client):
    client.delete_object(Bucket=bucket, Key=key)
    return True
