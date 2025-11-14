from flask import Flask, request, jsonify, url_for, redirect
from extensions import db, jwt
from models import User 
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from config import Config
from authlib.integrations.flask_client import OAuth
import os
import io
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import parse_model 
import mimetypes 
from PIL import Image
from parse_model import extract_receipt_data




app = Flask(__name__)
UPLOAD_FOLDER = 'uploads' 
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



# Initialize extensions
db.init_app(app)
jwt.init_app(app)

# Create DB tables
with app.app_context():
    db.create_all()

oauth = OAuth(app)

google = oauth.register(
    name='google',
    client_id='GOOGLE_CLIENT_ID',
    client_secret='GOOGLE_CLIENT_SECRET',
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)


# --------- Routes ---------

ALLOWED_MIMETYPES = ['image/jpeg', 'image/png', 'image/webp']

@app.route('/api/process-receipt', methods=['POST'])
def process_receipt():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
        
    mime_type, _ = mimetypes.guess_type(file.filename)
    
    if mime_type not in ALLOWED_MIMETYPES:
        return jsonify({'error': f'Unsupported file type: {mime_type}. Must be an image.'}), 415

    try:
        # Save the uploaded file temporarily
        image_bytes = file.read()
        temp_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        temp_image.save('temp_receipt.jpg')
        
        # Use your existing extract_receipt_data function
        result = extract_receipt_data('temp_receipt.jpg')
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal Server Error during image processing.'
        }), 500
# --- Google OAuth Endpoints ---

# Initiate Google Login
@app.route("/api/auth/google/login")
def google_login():
    """
    Redirects the user to Google's OAuth consent screen.
    """
    # Ensure the 'google_auth' endpoint is known
    redirect_uri = url_for("google_auth", _external=True)
    return google.authorize_redirect(redirect_uri)

# Handle Google Callback
@app.route("/api/auth/google/auth")
def google_auth():
    """
    Handles the callback from Google, retrieves user info, and logs them in/registers them.
    """
    try:
        # Fetch the access token and user information
        token = google.authorize_access_token()
        userinfo = google.parse_id_token(token)
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect("/login") 

    email = userinfo.get("email")
    user = User.query.filter_by(email=email).first()
    
    # Get name from Google userinfo
    google_name = userinfo.get("name")

    if user is None:
        # Register the new user using Google details
        user = User(
            
            username=google_name or email.split('@')[0], # Fallback to email prefix for username
            email=email,
            name=google_name, # Set the new name field
            
            is_oauth=True 
        )
        db.session.add(user)
        db.session.commit()


    # Create JWT for the user
    access_token = create_access_token(identity=str(user.id))

    
    return jsonify({"msg": "Google login successful", "access_token": access_token}), 200

# Registration
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    
    # Validation checks
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"msg": "Email already exists"}), 400

    # Handle birthdate string conversion to date object
    birthdate_str = data.get("birthdate")
    birthdate_obj = None
    if birthdate_str:
        try:
            # Assuming birthdate comes in ISO format (YYYY-MM-DD)
            from datetime import datetime
            birthdate_obj = datetime.strptime(birthdate_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"msg": "Invalid birthdate format. Use YYYY-MM-DD"}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        phone_number=data.get("phone_number"),
    
        name=data.get("name"),
        birthdate=birthdate_obj
    )
    
    # Ensure password exists for standard registration
    password = data.get("password")
    if not password:
        return jsonify({"msg": "Password is required for registration"}), 400
        
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({"msg": "User created successfully"}), 201


# Login with email lookup
@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    
    # Try finding user by username
    user = User.query.filter_by(username=data.get("username")).first()
    
    # If not found by username, try by email
    if not user and data.get("email"):
        user = User.query.filter_by(email=data["email"]).first()
        
    # Check if user exists AND if the password is correct
    if not user or not user.check_password(data.get("password")):
        return jsonify({"msg": "Bad credentials"}), 401
    
    # Prevent login if user is OAuth-only and they provide a password
    if user.is_oauth and user.password_hash is None:
        return jsonify({"msg": "Please use Google to log in"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({"access_token": access_token}), 200

# example
@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number
    })

# Run the app
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)