import face_recognition
import numpy as np
from PIL import Image
import io

class FaceRecognitionService:
    def __init__(self):
        self.tolerance = 0.6  
    
    def encode_face(self, image_data):
        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
                image_np = np.array(image)
            else:
                image_np = np.array(image_data)
            
            face_locations = face_recognition.face_locations(image_np)
            
            if len(face_locations) == 0:
                print("No face detected in image")
                return None
            
            face_encodings = face_recognition.face_encodings(image_np, face_locations)
            
            if len(face_encodings) > 0:
                return face_encodings[0]
            
            return None
        except Exception as e:
            print(f"Error encoding face: {e}")
            return None
    
    def compare_faces(self, known_encoding, unknown_encoding):
        if known_encoding is None or unknown_encoding is None:
            return False
        
        results = face_recognition.compare_faces(
            [known_encoding], 
            unknown_encoding, 
            tolerance=self.tolerance
        )
        return results[0]
    
    def find_matching_customer(self, captured_face_encoding, customer_encodings):
        if captured_face_encoding is None:
            return None
        
        for customer_id, known_encoding in customer_encodings.items():
            if known_encoding is not None:
                if self.compare_faces(known_encoding, captured_face_encoding):
                    return customer_id
        
        return None
    
    def extract_face_from_image(self, image_data):
        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data
            
            image_np = np.array(image)
            face_locations = face_recognition.face_locations(image_np)
            
            if len(face_locations) == 0:
                return None
            
            top, right, bottom, left = face_locations[0]
            
            # crop face
            padding = 20
            top = max(0, top - padding)
            left = max(0, left - padding)
            bottom = min(image_np.shape[0], bottom + padding)
            right = min(image_np.shape[1], right + padding)
            
            face_image = image_np[top:bottom, left:right]
            return Image.fromarray(face_image)
        except Exception as e:
            print(f"Error extracting face: {e}")
            return None