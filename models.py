from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
import uuid

# -------------------------
# User Model
# -------------------------
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    is_oauth = db.Column(db.Boolean, default=False)

    # Identity
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    # OAuth IDs
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    apple_id = db.Column(db.String(255), unique=True, nullable=True)

    # Security
    password_hash = db.Column(db.String(128), nullable=True)
    password_changed_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    is_two_factor_enabled = db.Column(db.Boolean, default=False)
    last_login = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(50), nullable=True)

    # Relationships
    roles = db.relationship("Role", secondary="user_role", backref="users")
    refresh_tokens = db.relationship("RefreshToken", backref="user", lazy=True)
    receipts = db.relationship('Receipt', backref='user', lazy=True)
    bill_splits = db.relationship('BillSplit', backref='user', lazy=True)
    login_attempts = db.relationship('LoginAttempt', backref='user', lazy=True)
    security_logs = db.relationship('SecurityLog', backref='user', lazy=True)
    activities = db.relationship('UserActivity', backref='user', lazy=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow(), onupdate=datetime.utcnow())

    # -------------------------
    # Password Helpers
    # -------------------------
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.utcnow()

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, resource, action):
        for role in self.roles:
            for perm in role.permissions:
                if perm.resource == resource and perm.action == action:
                    return True
        return False
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)


    def __repr__(self):
        return f"<User {self.username}>"

# -------------------------
# Role & Permission Models
# -------------------------
class Role(db.Model):
    role_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    permissions = db.relationship("Permission", secondary="role_permission", backref="roles")
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f"<Role {self.name}>"

class Permission(db.Model):
    permission_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    resource = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def __repr__(self):
        return f"<Permission {self.name}:{self.action}>"

class UserRole(db.Model):
    __tablename__ = "user_role"
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), primary_key=True)
    role_id = db.Column(db.String(36), db.ForeignKey("role.role_id"), primary_key=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow())
    assigned_by = db.Column(db.String(36), nullable=True)

class RolePermission(db.Model):
    __tablename__ = "role_permission"
    role_id = db.Column(db.String(36), db.ForeignKey("role.role_id"), primary_key=True)
    permission_id = db.Column(db.String(36), db.ForeignKey("permission.permission_id"), primary_key=True)

# -------------------------
# Refresh Token
# -------------------------
class RefreshToken(db.Model):
    token_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, default=False)
    replaced_by = db.Column(db.String(36), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

# -------------------------
# One-time Auth Actions
# -------------------------
class AuthAction(db.Model):
    action_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    action_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

# -------------------------
# Login Attempts
# -------------------------
class LoginAttempt(db.Model):
    attempt_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(255), nullable=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow())

# -------------------------
# Security Log
# -------------------------
class SecurityLog(db.Model):
    log_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=True)
    event_type = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

# -------------------------
# User Activity
# -------------------------
class UserActivity(db.Model):
    activity_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("user.id"), nullable=False)
    activity_type = db.Column(db.String(100), nullable=False)
    resource = db.Column(db.String(100), nullable=True)
    metaData = db.Column(db.JSON, nullable=True)
    performed_at = db.Column(db.DateTime, default=datetime.utcnow())

# -------------------------
# Receipt Model
class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    
    store_name = db.Column(db.String(200), nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    subtotal_amount = db.Column(db.Float, nullable=True)
    tax_amount = db.Column(db.Float, nullable=True)
    receipt_date = db.Column(db.String(100), nullable=True)
    raw_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    processed_at = db.Column(db.DateTime, default=datetime.utcnow())
    image_path = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'store_name': self.store_name,
            'total_amount': self.total_amount,
            'subtotal_amount': self.subtotal_amount,
            'tax_amount': self.tax_amount,
            'receipt_date': self.receipt_date,
            'raw_data': self.raw_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class BillSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    
    receipt_data = db.Column(db.JSON, nullable=True)
    participants = db.Column(db.JSON, nullable=True)  
    split_method = db.Column(db.String(50), default='itemized')  
    tax_rate = db.Column(db.Float, default=0.0)
    tip_percentage = db.Column(db.Float, default=0.0)
    split_result = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'receipt_data': self.receipt_data,
            'participants': self.participants,
            'split_method': self.split_method,
            'tax_rate': self.tax_rate,
            'tip_percentage': self.tip_percentage,
            'split_result': self.split_result,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
