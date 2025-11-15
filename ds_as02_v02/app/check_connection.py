"""
Setup Script
Initialize database and storage for the coffeehouse system
"""
import os
from database_manager import DatabaseManager
from storage_manager import StorageManager

from dotenv import load_dotenv
load_dotenv(dotenv_path="configs/.env")

def setup_system():
    """Initialize the system"""
    print("=" * 50)
    print("Coffeehouse Face Recognition System Setup")
    print("=" * 50)
    
    # Initialize MongoDB
    print("\n[1/3] Initializing MongoDB...")
    try:
        db_manager = DatabaseManager()
        
        print("✓ MongoDB connected successfully")
        print(f"  - Database: {db_manager.db.name}")
        print(f"  - Collections: customers, orders")
        
        # Check for existing customers
        customer_count = db_manager.customers.count_documents({})
        print(f"  - Existing customers: {customer_count}")
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False
    
    # Initialize MinIO
    print("\n[2/3] Initializing MinIO storage...")
    try:
        storage_manager = StorageManager()
        print("✓ MinIO connected successfully")
        print(f"  - Endpoint: {os.getenv('MINIO_ENDPOINT', 'localhost:9000')}")
        print(f"  - Bucket: {storage_manager.bucket_name}")
    except Exception as e:
        print(f"✗ MinIO connection failed: {e}")
        print("  Please ensure MinIO is running on localhost:9000")
        return False
    return True

if __name__ == "__main__":
    setup_system()