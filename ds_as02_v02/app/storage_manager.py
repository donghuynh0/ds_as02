import os
import io
from minio import Minio
from minio.error import S3Error
from PIL import Image
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "configs" / ".env"
load_dotenv(dotenv_path=env_path)

class StorageManager:
    def __init__(self):
        endpoint = os.getenv('MINIO_ENDPOINT')
        access_key = os.getenv('MINIO_ACCESS_KEY')
        secret_key = os.getenv('MINIO_SECRET_KEY')
        
        print(f"Connecting to MinIO: {endpoint}")
        print(f"Access Key: {access_key}")
        
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket_name = os.getenv('MINIO_BUCKET', 'customer-faces')
        
        # Create bucket if not exists
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                print(f"Created bucket: {self.bucket_name}")
            else:
                print(f"Bucket exists: {self.bucket_name}")
        except Exception as e:
            print(f"Error checking/creating bucket: {e}")
    
    def upload_face_image(self, customer_id, image_data):
        try:
            object_name = f"{customer_id}.jpg"
            
            # Convert to bytes if PIL Image
            if isinstance(image_data, Image.Image):
                img_byte_arr = io.BytesIO()
                image_data.save(img_byte_arr, format='JPEG')
                img_byte_arr.seek(0)
                data = img_byte_arr
                length = img_byte_arr.getbuffer().nbytes
            else:
                data = io.BytesIO(image_data)
                length = len(image_data)
            
            self.client.put_object(
                self.bucket_name,
                object_name,
                data,
                length,
                content_type='image/jpeg'
            )
            return object_name
        except S3Error as e:
            print(f"Error uploading image: {e}")
            return None
    
    def download_face_image(self, customer_id):
        try:
            object_name = f"{customer_id}.jpg"
            response = self.client.get_object(self.bucket_name, object_name)
            image_data = response.read()
            response.close()
            response.release_conn()
            return image_data
        except S3Error as e:
            print(f"Error downloading image: {e}")
            return None
    
    def get_face_image_path(self, customer_id):
        return f"{self.bucket_name}/{customer_id}.jpg"
    
    def delete_face_image(self, customer_id):
        try:
            object_name = f"{customer_id}.jpg"
            self.client.remove_object(self.bucket_name, object_name)
            return True
        except S3Error as e:
            print(f"Error deleting image: {e}")
            return False