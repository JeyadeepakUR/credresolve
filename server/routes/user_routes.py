from flask import Blueprint, request, jsonify
from middleware.auth import auth_required

def create_user_routes(user_service, balance_service):
    bp = Blueprint('user_routes', __name__, url_prefix='/api/users')

    @bp.post('/')
    def create_user():
        data = request.get_json() or {}
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Name, email and password are required'
                }
            }), 400

        try:
            user = user_service.create_user(name, email, password)
            return jsonify(user), 201
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'CREATE_USER_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'CREATE_USER_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<user_id>')
    @auth_required
    def get_user(user_id):
        try:
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': 'User not found'
                    }
                }), 404
            return jsonify(user)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_USER_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/')
    @auth_required
    def get_users():
        try:
            users = user_service.get_all_users()
            return jsonify(users)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_USERS_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<user_id>/balances')
    @auth_required
    def get_user_balances(user_id):
        try:
            user = user_service.get_user(user_id)
            if not user:
                return jsonify({
                    'error': {
                        'code': 'USER_NOT_FOUND',
                        'message': 'User not found'
                    }
                }), 404
            balances = balance_service.get_user_balances(user_id)
            return jsonify({
                'userId': user_id,
                'owes': balances['owes'],
                'owed': balances['owed'],
                'netBalance': balances['netBalance']
            })
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_BALANCES_ERROR',
                    'message': str(err)
                }
            }), 500

    return bp
