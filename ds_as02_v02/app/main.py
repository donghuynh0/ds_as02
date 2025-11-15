"""
Flask Web Application for Coffeehouse Face Recognition System
Provides both client and staff interfaces
"""
from flask import Flask, render_template, Response, jsonify, request
from backend_server import BackendServer
from database_manager import DatabaseManager
import cv2
import io
from PIL import Image
import time
import base64

app = Flask(__name__)
backend = BackendServer()
db_manager = DatabaseManager()

# Global variables
camera = None
last_capture_time = 0
capture_cooldown = 3  # seconds between auto-captures

BRANCH_NAME = "Downtown Branch"

def get_camera():
    """Get camera instance"""
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera

def generate_frames():
    """Generate video frames for streaming"""
    global last_capture_time
    
    cam = get_camera()
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    
    while True:
        success, frame = cam.read()
        if not success:
            break
        
        # Detect faces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        # Draw rectangles around faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Redirect to client interface"""
    menu_items = db_manager.get_all_menu_items()
    return render_template('client.html', menu_items=menu_items, branch_name=BRANCH_NAME)

@app.route('/client')
def client():
    """Client interface - menu and automatic face capture"""
    menu_items = db_manager.get_all_menu_items()
    return render_template('client.html', menu_items=menu_items, branch_name=BRANCH_NAME)

@app.route('/staff')
def staff():
    """Staff interface - customer history and management"""
    return render_template('staff.html', branch_name=BRANCH_NAME)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/capture_face', methods=['POST'])
def capture_face():
    """Capture and process face from camera"""
    global last_capture_time
    
    current_time = time.time()
    
    # Check cooldown
    if current_time - last_capture_time < capture_cooldown:
        return jsonify({
            'status': 'cooldown',
            'message': 'Please wait before next capture'
        })
    
    cam = get_camera()
    success, frame = cam.read()
    
    if not success:
        return jsonify({
            'status': 'error',
            'message': 'Failed to capture image'
        })
    
    # Convert frame to PIL Image
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    
    # Process face recognition
    response = backend.process_face_recognition_request(
        img_byte_arr.getvalue(),
        BRANCH_NAME
    )
    
    last_capture_time = current_time
    
    return jsonify(response)

@app.route('/api/place_order', methods=['POST'])
def place_order():
    """Place order for customer"""
    data = request.json
    
    customer_id = data.get('customer_id')
    items = data.get('items', [])
    total_price = data.get('total_price', 0)
    recapture = data.get('recapture', False)
    
    if not customer_id or not items:
        return jsonify({
            'status': 'error',
            'message': 'Missing customer_id or items'
        })
    
    # If recapture requested for new customer
    if recapture:
        cam = get_camera()
        success, frame = cam.read()
        
        if success:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            
            # Extract and save face
            face_image = backend.face_service.extract_face_from_image(img_byte_arr.getvalue())
            if face_image:
                backend.storage_manager.upload_face_image(customer_id, face_image)
    
    result = backend.add_order_for_customer(
        customer_id,
        items,
        total_price,
        BRANCH_NAME
    )
    
    return jsonify(result)

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get all customers (for staff interface)"""
    customers = backend.db_manager.get_all_customers()
    
    # Convert to JSON-serializable format
    customers_list = []
    for customer in customers:
        customer_dict = {
            'customer_id': customer['customer_id'],
            'name': customer['name'],
            'total_visits': customer.get('total_visits', 0),
            'last_visit': customer.get('last_visit').strftime('%Y-%m-%d %H:%M:%S') if customer.get('last_visit') else 'N/A',
            'created_at': customer.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if customer.get('created_at') else 'N/A'
        }
        customers_list.append(customer_dict)
    
    return jsonify(customers_list)

@app.route('/api/customer/<customer_id>', methods=['GET'])
def get_customer_details(customer_id):
    """Get detailed customer information"""
    customer = backend.db_manager.get_customer(customer_id)
    
    if not customer:
        return jsonify({
            'status': 'error',
            'message': 'Customer not found'
        })
    
    # Get order history
    order_history = backend.db_manager.get_customer_order_history(customer_id, limit=10)
    
    customer_data = {
        'customer_id': customer['customer_id'],
        'name': customer['name'],
        'total_visits': customer.get('total_visits', 0),
        'last_visit': customer.get('last_visit').strftime('%Y-%m-%d %H:%M:%S') if customer.get('last_visit') else 'N/A',
        'created_at': customer.get('created_at').strftime('%Y-%m-%d %H:%M:%S') if customer.get('created_at') else 'N/A',
        'order_history': []
    }
    
    for order in order_history:
        order_dict = {
            'order_date': order.get('order_date').strftime('%Y-%m-%d %H:%M:%S') if order.get('order_date') else 'N/A',
            'items': order.get('items', []),
            'total_price': order.get('total_price', 0),
            'branch': order.get('branch', 'Unknown')
        }
        customer_data['order_history'].append(order_dict)
    
    return jsonify(customer_data)

@app.route('/api/customer/<customer_id>/image', methods=['GET'])
def get_customer_image(customer_id):
    """Get customer face image"""
    try:
        image_data = backend.storage_manager.download_face_image(customer_id)
        
        if image_data:
            return Response(image_data, mimetype='image/jpeg')
        else:
            # Return default placeholder image (1x1 transparent pixel)
            return Response(
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
                mimetype='image/png'
            )
    except Exception as e:
        return Response(
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82',
            mimetype='image/png'
        )

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)