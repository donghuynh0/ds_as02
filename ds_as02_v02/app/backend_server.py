import uuid
from datetime import datetime
from database_manager import DatabaseManager
from storage_manager import StorageManager
from face_recognition_service import FaceRecognitionService

class BackendServer:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.storage_manager = StorageManager()
        self.face_service = FaceRecognitionService()
        self.customer_encodings = {}
        self._load_customer_encodings()
    
    def _load_customer_encodings(self):
        customers = self.db_manager.get_all_customers()
        
        for customer in customers:
            customer_id = customer['customer_id']
            face_image_data = self.storage_manager.download_face_image(customer_id)
            
            if face_image_data:
                encoding = self.face_service.encode_face(face_image_data)
                if encoding is not None:
                    self.customer_encodings[customer_id] = encoding
            
    def process_face_recognition_request(self, image_data, branch_name):        
        # encode face
        captured_encoding = self.face_service.encode_face(image_data)
        
        if captured_encoding is None:
            return {
                'status': 'error',
                'message': 'No face detected in image'
            }
        
        # find 
        matched_customer_id = self.face_service.find_matching_customer(
            captured_encoding, 
            self.customer_encodings
        )
        
        if matched_customer_id:            
            customer = self.db_manager.get_customer(matched_customer_id)
            
            # get orders
            latest_order = self.db_manager.get_latest_order(matched_customer_id)
            
            # get history
            order_history = self.db_manager.get_customer_order_history(matched_customer_id, limit=5)
            
            self.db_manager.update_customer_visit(matched_customer_id)
            
            response = {
                'status': 'recognized',
                'customer_id': matched_customer_id,
                'customer_name': customer.get('name', 'Unknown'),
                'total_visits': customer.get('total_visits', 0),
                'last_visit': customer.get('last_visit', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                'latest_order': self._format_order(latest_order) if latest_order else None,
                'order_history': [self._format_order(order) for order in order_history]
            }
            
            return response
        else:
            customer_id = str(uuid.uuid4())
            
            # save face
            face_image = self.face_service.extract_face_from_image(image_data)
            if face_image:
                image_path = self.storage_manager.upload_face_image(customer_id, face_image)
            else:
                image_path = self.storage_manager.upload_face_image(customer_id, image_data)
            
            
            self.db_manager.create_customer(
                customer_id=customer_id,
                name=f"Customer_{customer_id[:8]}",
                face_image_path=image_path
            )
            
            
            self.customer_encodings[customer_id] = captured_encoding
            
            response = {
                'status': 'new_customer',
                'customer_id': customer_id,
                'customer_name': f"Customer_{customer_id[:8]}",
                'message': 'New customer registered successfully',
                'total_visits': 1
            }
            
            return response
    
    def _format_order(self, order):
        if not order:
            return None
        
        return {
            'order_date': order.get('order_date', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
            'items': order.get('items', []),
            'total_price': order.get('total_price', 0),
            'branch': order.get('branch', 'Unknown')
        }
    
    def add_order_for_customer(self, customer_id, items, total_price, branch):
        order_id = self.db_manager.add_order(customer_id, items, total_price, branch)
        return {'status': 'success', 'order_id': order_id}
    
    def close(self):
        self.db_manager.close()