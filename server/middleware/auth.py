import jwt
import os
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret')

def issue_token(user):
    """Generate JWT token for user"""
    return jwt.encode(
        {'id': user['id'], 'email': user['email']},
        JWT_SECRET,
        algorithm='HS256'
    )

def auth_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header[7:] if auth_header.startswith('Bearer ') else None
        
        if not token:
            return jsonify({
                'error': {'code': 'UNAUTHORIZED', 'message': 'Authentication token missing'}
            }), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = {'id': payload['id'], 'email': payload['email']}
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({
                'error': {'code': 'INVALID_TOKEN', 'message': 'Token has expired'}
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid or expired token'}
            }), 401
    
    return decorated_function
