from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Date, JSON
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_oauth = db.Column(db.Boolean, default=False)
    
    # Identity
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    name = db.Column(db.String(100), nullable=True) 
    
    birthdate = db.Column(db.Date, nullable=True) 
    
    # Social Login Fields
    google_id = db.Column(db.String(255), unique=True, nullable=True)
    apple_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Security Fields
    password_hash = db.Column(db.String(128), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)

    # Relationship to receipts
    receipts = db.relationship('Receipt', backref='user', lazy=True)

    def set_password(self, password):
        """Hashes the password using Werkzeug's security functions."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks the plain password against the stored hash."""
        # Check if a hash exists before attempting to compare
        if self.password_hash is None:
            return False 
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Receipt data
    store_name = db.Column(db.String(200), nullable=True)
    total_amount = db.Column(db.Float, nullable=True)
    subtotal_amount = db.Column(db.Float, nullable=True)
    tax_amount = db.Column(db.Float, nullable=True)
    receipt_date = db.Column(db.String(100), nullable=True)
    
    # Store the full parsed data as JSON for flexibility
    raw_data = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Optional: Store the image path if you want to save the actual image
    image_path = db.Column(db.String(500), nullable=True)

    def to_dict(self):
        """Convert receipt to dictionary for JSON response"""
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

    def __repr__(self):
        return f'<Receipt {self.id} - {self.store_name}>'
    

class BillSplit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Split configuration
    receipt_data = db.Column(db.JSON, nullable=True)
    # List of participant names
    participants = db.Column(db.JSON, nullable=True)  
    split_method = db.Column(db.String(50), default='itemized')  
    tax_rate = db.Column(db.Float, default=0.0)
    tip_percentage = db.Column(db.Float, default=0.0)
    
    # Split results
    split_result = db.Column(db.JSON, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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
    
    def __repr__(self):
        return f'<BillSplit {self.id}>'