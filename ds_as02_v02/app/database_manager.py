import os
from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).resolve().parent.parent / "configs" / ".env"
load_dotenv(dotenv_path=env_path)

class DatabaseManager:
    def __init__(self):
        self.client = MongoClient(os.getenv('MONGO_URI'))
        self.db = self.client[os.getenv('MONGO_DB')]
        self.customers = self.db.customers
        self.orders = self.db.orders
        self.menu = self.db.menu
        
        # Create indexes for better performance
        self.customers.create_index('customer_id', unique=True)
        self.orders.create_index('customer_id')
        self.menu.create_index('item_name', unique=True)
    
    def create_customer(self, customer_id, name, face_image_path):
        customer = {
            'customer_id': customer_id,
            'name': name,
            'face_image_path': face_image_path,
            'created_at': datetime.now(),
            'last_visit': datetime.now(),
            'total_visits': 1
        }
        result = self.customers.insert_one(customer)
        return str(result.inserted_id)
    
    def get_customer(self, customer_id):
        return self.customers.find_one({'customer_id': customer_id})
    
    def get_all_customers(self):
        return list(self.customers.find())
    
    def update_customer_visit(self, customer_id):
        self.customers.update_one(
            {'customer_id': customer_id},
            {
                '$set': {'last_visit': datetime.now()},
                '$inc': {'total_visits': 1}
            }
        )
    
    def add_order(self, customer_id, items, total_price, branch):
        order = {
            'customer_id': customer_id,
            'items': items,
            'total_price': total_price,
            'branch': branch,
            'order_date': datetime.now()
        }
        result = self.orders.insert_one(order)
        return str(result.inserted_id)
    
    def get_latest_order(self, customer_id):
        return self.orders.find_one(
            {'customer_id': customer_id},
            sort=[('order_date', -1)]
        )
    
    def get_customer_order_history(self, customer_id, limit=10):
        return list(self.orders.find(
            {'customer_id': customer_id}
        ).sort('order_date', -1).limit(limit))
    
    def get_all_menu_items(self):
        """Get all menu items from database"""
        menu_items = {}
        for item in self.menu.find():
            menu_items[item['item_name']] = item['price']
        return menu_items
    
    def close(self):
        self.client.close()