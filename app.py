from flask import Flask, request, jsonify, url_for, redirect
from extensions import db, jwt
from models import (
    User, Role, Permission, UserRole, RefreshToken, AuthAction, 
    LoginAttempt, SecurityLog, UserActivity, Receipt, BillSplit
)
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from config import Config
from authlib.integrations.flask_client import OAuth
import os
import io
import mimetypes
from PIL import Image
from parse_model import extract_receipt_data
from datetime import datetime, timedelta
from functools import wraps
from auth.decorator import role_required
import uuid

# ---------------- App Setup ----------------
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_MIMETYPES = ['image/jpeg', 'image/png', 'image/webp']

app.config.from_object(Config)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize extensions
db.init_app(app)
jwt.init_app(app)

with app.app_context():
    db.create_all()

# ---------------- OAuth Setup ----------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='GOOGLE_CLIENT_ID',
    client_secret='GOOGLE_CLIENT_SECRET',
    access_token_url='https://oauth2.googleapis.com/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'}
)

# ---------------- Helper Functions ----------------

def log_login_attempt(user_id, email, success, failure_reason=None):
    """Record a login attempt"""
    attempt = LoginAttempt(
        attempt_id=str(uuid.uuid4()),
        user_id=user_id,
        email=email,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=success,
        failure_reason=failure_reason,
        attempted_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.commit()


# ---------------- Admin Endpoints----------------
@app.route("/api/admin/users", methods=["GET"])
@role_required("admin")
def admin_get_users():
    users = User.query.all()
    return jsonify([
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "is_active": u.is_active,
            "roles": [r.name for r in u.roles]
        } for u in users
    ])


@app.route("/api/admin/users/<user_id>/status", methods=["PATCH"])
@role_required("admin")
def admin_toggle_user(user_id):
    data = request.get_json()
    user = User.query.get_or_404(user_id)

    user.is_active = data.get("is_active", user.is_active)
    db.session.commit()

    return jsonify({"msg": "User status updated"})


@app.route("/api/admin/users/<user_id>/roles", methods=["POST"])
@role_required("admin")
def admin_assign_role(user_id):
    data = request.get_json()
    role_name = data.get("role")

    user = User.query.get_or_404(user_id)
    role = Role.query.filter_by(name=role_name).first()

    if not role:
        return jsonify({"msg": "Role not found"}), 404

    if role not in user.roles:
        user.roles.append(role)
        db.session.commit()

    return jsonify({"msg": f"Role '{role_name}' assigned"})



# ---------------- Auth Endpoints ----------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"msg": "Username already exists"}), 400
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"msg": "Email already exists"}), 400

    birthdate_obj = None
    if data.get("birthdate"):
        try:
            birthdate_obj = datetime.strptime(data["birthdate"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"msg": "Invalid birthdate format. Use YYYY-MM-DD"}), 400

    user = User(
        id=str(uuid.uuid4()),
        username=data["username"],
        email=data["email"],
        name=data.get("name"),
        phone_number=data.get("phone_number"),
        birthdate=birthdate_obj,
        is_oauth=False
    )

    password = data.get("password")
    if not password:
        return jsonify({"msg": "Password is required"}), 400
    user.set_password(password)

    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created successfully", "user_id": user.id}), 201

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email_or_username = data.get("username") or data.get("email")
    user = User.query.filter(
        (User.username == email_or_username) | (User.email == email_or_username)
    ).first()

    if not user or not user.check_password(data.get("password")):
        log_login_attempt(user.id if user else None, email_or_username, False, "Invalid credentials")
        return jsonify({"msg": "Bad credentials"}), 401

    if user.is_oauth and not user.password_hash:
        return jsonify({"msg": "Please login using Google"}), 401

    access_token = create_access_token(identity=user.id)
    refresh_token_str = create_refresh_token(identity=user.id)

    # Store refresh token hash in DB
    refresh_token = RefreshToken(
        token_id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=refresh_token_str,
        expires_at=datetime.utcnow() + timedelta(days=30),
        revoked=False,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        created_at=datetime.utcnow()
    )
    db.session.add(refresh_token)
    db.session.commit()

    log_login_attempt(user.id, email_or_username, True)
    return jsonify({"access_token": access_token, "refresh_token": refresh_token_str}), 200

@app.route("/api/auth/logout", methods=["POST"])
@jwt_required()
def logout():
    current_user = get_jwt_identity()
    data = request.get_json() or {}
    refresh_token_str = data.get("refresh_token")

    if not refresh_token_str:
        return jsonify({"msg": "Refresh token required"}), 400

    token = RefreshToken.query.filter_by(
        user_id=current_user,
        token_hash=refresh_token_str,
        revoked=False
    ).first()

    if token:
        token.revoked = True
        db.session.commit()
        return jsonify({"msg": "Logged out successfully"}), 200

    return jsonify({"msg": "Token not found or already revoked"}), 404


@app.route("/api/auth/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({"access_token": access_token}), 200

@app.route("/api/auth/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone_number": user.phone_number
    })

# ---------------- Google OAuth ----------------
@app.route("/api/auth/google/login")
def google_login():
    redirect_uri = url_for("google_auth", _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route("/api/auth/google/auth")
def google_auth():
    try:
        token = google.authorize_access_token()
        userinfo = google.parse_id_token(token)
    except Exception as e:
        print(f"OAuth error: {e}")
        return redirect("/login")

    email = userinfo.get("email")
    user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            id=str(uuid.uuid4()),
            username=userinfo.get("name") or email.split("@")[0],
            email=email,
            name=userinfo.get("name"),
            google_id=userinfo.get("sub"),
            is_oauth=True
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return jsonify({"msg": "Google login successful", "access_token": access_token}), 200

# ---------------- Receipt & Bill Split Endpoints ----------------
@app.route('/api/process-receipt', methods=['POST'])
@jwt_required()
def process_receipt():
    user = User.query.get(get_jwt_identity())
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    mime_type, _ = mimetypes.guess_type(file.filename)
    if mime_type not in ALLOWED_MIMETYPES:
        return jsonify({'error': f'Unsupported file type: {mime_type}'}), 415

    try:
        image_bytes = file.read()
        temp_image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"receipt_{user.id}_{timestamp}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        temp_image.save(filepath)

        result = extract_receipt_data(filepath)

        receipt = Receipt(
            user_id=user.id,
            store_name=result.get('store_name', ''),
            total_amount=float(result.get('total', 0)) if result.get('total') else None,
            subtotal_amount=float(result.get('subtotal', 0)) if result.get('subtotal') else None,
            tax_amount=float(result.get('tax', 0)) if result.get('tax') else None,
            receipt_date=result.get('date', ''),
            raw_data=result,
            image_path=filepath
        )
        db.session.add(receipt)
        db.session.commit()

        return jsonify({"success": True, "receipt_id": receipt.id, "data": result}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- Bill Split Endpoints ----------------
@app.route('/api/split-bill', methods=['POST'])
@jwt_required()
def split_bill():
    data = request.get_json()
    receipt_data = data.get('receipt_data')
    participants = data.get('participants', [])
    split_method = data.get('split_method', 'itemized')
    tax_rate = data.get('tax_rate', 0)
    tip_percentage = data.get('tip_percentage', 0)

    if not receipt_data or not participants:
        return jsonify({"error": "Missing data"}), 400

    user = User.query.get(get_jwt_identity())
    try:
        if split_method == 'even':
            from bill_splitting_logic import calculate_even_split
            result = calculate_even_split(float(receipt_data.get('total', 0)), len(participants))
        else:
            from bill_splitting_logic import split_receipt_items
            result = split_receipt_items(receipt_data, participants, tax_rate, tip_percentage)

        bill_split = BillSplit(
            user_id=user.id,
            receipt_data=receipt_data,
            participants=participants,
            split_result=result,
            split_method=split_method,
            tax_rate=tax_rate,
            tip_percentage=tip_percentage
        )
        db.session.add(bill_split)
        db.session.commit()

        return jsonify({"success": True, "split_result": result, "bill_split_id": bill_split.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------- Run App ----------------
'''if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)'''
