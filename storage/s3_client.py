"""S3-compatible storage client wrapper"""
import os
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from typing import Optional, BinaryIO
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """Wrapper around boto3 for S3-compatible storage"""
    
    def __init__(self):
        endpoint = os.getenv("S3_ENDPOINT", "http://localhost:9000")
        access_key = os.getenv("S3_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("S3_SECRET_KEY", "minioadmin")
        bucket_name = os.getenv("S3_BUCKET", "documents")
        region = os.getenv("S3_REGION", "us-east-1")
        
        self.bucket_name = bucket_name
        self.client = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version='s3v4')
        )
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError:
            try:
                self.client.create_bucket(Bucket=self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            except ClientError as e:
                logger.error(f"Failed to create bucket: {e}")
                raise
    
    def upload_file(self, file_obj: BinaryIO, key: str, content_type: Optional[str] = None) -> str:
        """Upload a file to S3"""
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type
        
        self.client.upload_fileobj(
            file_obj,
            self.bucket_name,
            key,
            ExtraArgs=extra_args
        )
        return key
    
    def download_file(self, key: str, file_path: str):
        """Download a file from S3 to local path"""
        self.client.download_file(self.bucket_name, key, file_path)
    
    def get_file(self, key: str) -> bytes:
        """Get file contents as bytes"""
        response = self.client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read()
    
    def delete_file(self, key: str):
        """Delete a file from S3"""
        self.client.delete_object(Bucket=self.bucket_name, Key=key)
    
    def generate_presigned_url(self, key: str, expiration: int = 3600) -> str:
        """Generate a presigned URL for upload/download"""
        try:
            url = self.client.generate_presigned_url(
                'put_object' if 'raw' in key else 'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise
    
    def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3"""
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False

