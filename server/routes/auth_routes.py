from flask import Blueprint, request, jsonify
from middleware.auth import issue_token, auth_required

def create_auth_routes(user_service):
    bp = Blueprint('auth_routes', __name__, url_prefix='/api/auth')

    @bp.post('/register')
    def register():
        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Name, email, and password are required'
                }
            }), 400

        try:
            user = user_service.create_user(name, email, password)
            token = issue_token(user)
            return jsonify({'user': user, 'token': token}), 201
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'REGISTER_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'REGISTER_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.post('/login')
    def login():
        data = request.get_json() or {}
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Email and password are required'
                }
            }), 400

        try:
            user = user_service.verify_password(email, password)
            if not user:
                return jsonify({
                    'error': {
                        'code': 'INVALID_CREDENTIALS',
                        'message': 'Invalid email or password'
                    }
                }), 401

            token = issue_token(user)
            return jsonify({'user': user, 'token': token})
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'LOGIN_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/me')
    @auth_required
    def me():
        user = user_service.get_user(request.user['id'])
        return jsonify({'user': user})

    return bp
