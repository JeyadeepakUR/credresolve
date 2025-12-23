from flask import Blueprint, request, jsonify
from middleware.auth import auth_required

def create_group_routes(group_service, expense_service, balance_service):
    bp = Blueprint('group_routes', __name__, url_prefix='/api/groups')

    @bp.post('/')
    @auth_required
    def create_group():
        data = request.get_json() or {}
        name = data.get('name')
        description = data.get('description', '')
        created_by = data.get('createdBy') or getattr(request, 'user', {}).get('id')

        if not name or not created_by:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Name and createdBy are required'
                }
            }), 400

        try:
            group = group_service.create_group(name, description, created_by)
            return jsonify(group), 201
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'CREATE_GROUP_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'CREATE_GROUP_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<group_id>')
    @auth_required
    def get_group(group_id):
        try:
            group = group_service.get_group(group_id)
            if not group:
                return jsonify({
                    'error': {
                        'code': 'GROUP_NOT_FOUND',
                        'message': 'Group not found'
                    }
                }), 404
            return jsonify(group)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_GROUP_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/')
    @auth_required
    def get_groups():
        try:
            groups = group_service.get_all_groups()
            return jsonify(groups)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_GROUPS_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.post('/<group_id>/members')
    @auth_required
    def add_member(group_id):
        data = request.get_json() or {}
        user_id = data.get('userId')

        if not user_id:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'userId is required'
                }
            }), 400

        try:
            added = group_service.add_member(group_id, user_id)
            if not added:
                return jsonify({
                    'error': {
                        'code': 'MEMBER_EXISTS',
                        'message': 'User is already a member'
                    }
                }), 400
            group = group_service.get_group(group_id)
            return jsonify(group)
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'ADD_MEMBER_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'ADD_MEMBER_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<group_id>/expenses')
    @auth_required
    def get_group_expenses(group_id):
        try:
            group = group_service.get_group(group_id)
            if not group:
                return jsonify({
                    'error': {
                        'code': 'GROUP_NOT_FOUND',
                        'message': 'Group not found'
                    }
                }), 404
            expenses = expense_service.get_group_expenses(group_id)
            return jsonify(expenses)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_EXPENSES_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<group_id>/balances')
    @auth_required
    def get_group_balances(group_id):
        try:
            group = group_service.get_group(group_id)
            if not group:
                return jsonify({
                    'error': {
                        'code': 'GROUP_NOT_FOUND',
                        'message': 'Group not found'
                    }
                }), 404
            balances = balance_service.get_group_balances(group_id)
            return jsonify(balances)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_BALANCES_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<group_id>/balances/simplified')
    @auth_required
    def get_simplified_balances(group_id):
        try:
            group = group_service.get_group(group_id)
            if not group:
                return jsonify({
                    'error': {
                        'code': 'GROUP_NOT_FOUND',
                        'message': 'Group not found'
                    }
                }), 404
            simplified = balance_service.get_simplified_balances(group_id)
            return jsonify({
                'groupId': group_id,
                'simplifiedTransactions': simplified,
                'transactionCount': len(simplified)
            })
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'SIMPLIFY_BALANCES_ERROR',
                    'message': str(err)
                }
            }), 500

    return bp
