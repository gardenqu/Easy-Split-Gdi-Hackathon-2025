from app import app
from extensions import db
from flask_migrate import Migrate

# import all your models so Flask-Migrate sees them
from models import (
    User, Role, Permission, UserRole, RefreshToken, AuthAction, 
    LoginAttempt, SecurityLog, UserActivity, Receipt, BillSplit
)

migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
