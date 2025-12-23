import bcrypt
import uuid
from db import get_db

SALT_ROUNDS = 10

def map_row_to_user(row):
    """Convert database row to user dict"""
    if not row:
        return None
    return {
        'id': row['id'],
        'name': row['name'],
        'email': row['email'],
        'createdAt': row['created_at']
    }

class UserService:
    """Service for managing users with SQLite persistence"""
    
    def __init__(self):
        pass
    
    def create_user(self, name, email, password):
        """Create a new user with hashed password"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if email exists
        existing = self.get_user_by_email(email)
        if existing:
            conn.close()
            raise ValueError('Email already exists')
        
        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        cursor.execute(
            'INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)',
            (user_id, name, email, password_hash)
        )
        conn.commit()
        
        created = self.get_user(user_id)
        conn.close()
        return created
    
    def get_user(self, user_id):
        """Get user by ID"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return map_row_to_user(row)
    
    def get_user_by_email(self, email):
        """Get user by email"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        return map_row_to_user(row)
    
    def get_all_users(self):
        """Get all users"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [map_row_to_user(row) for row in rows]
    
    def user_exists(self, user_id):
        """Check if user exists"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def validate_users(self, user_ids):
        """Validate that all user IDs exist"""
        missing_users = [uid for uid in user_ids if not self.user_exists(uid)]
        return {
            'valid': len(missing_users) == 0,
            'missingUsers': missing_users
        }
    
    def verify_password(self, email, password):
        """Verify user password and return user if valid"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        password_hash = row['password_hash']
        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            return map_row_to_user(row)
        
        return None
