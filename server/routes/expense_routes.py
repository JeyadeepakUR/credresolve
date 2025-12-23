from flask import Blueprint, request, jsonify
from middleware.auth import auth_required

def create_expense_routes(expense_service):
    bp = Blueprint('expense_routes', __name__, url_prefix='/api/expenses')

    @bp.post('/')
    @auth_required
    def add_expense():
        data = request.get_json() or {}
        group_id = data.get('groupId')
        description = data.get('description')
        total_amount = data.get('totalAmount')
        paid_by = data.get('paidBy') or getattr(request, 'user', {}).get('id')
        split_type = data.get('splitType')
        splits = data.get('splits')

        if not group_id or not description or total_amount is None or not paid_by or not split_type or splits is None:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'All fields are required: groupId, description, totalAmount, paidBy, splitType, splits'
                }
            }), 400

        try:
            result = expense_service.add_expense({
                'groupId': group_id,
                'description': description,
                'totalAmount': total_amount,
                'paidBy': paid_by,
                'splitType': split_type,
                'splits': splits
            })
            return jsonify({
                'expense': result['expense'],
                'updatedBalances': result['balances']
            }), 201
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'ADD_EXPENSE_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'ADD_EXPENSE_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<expense_id>')
    @auth_required
    def get_expense(expense_id):
        try:
            expense = expense_service.get_expense(expense_id)
            if not expense:
                return jsonify({
                    'error': {
                        'code': 'EXPENSE_NOT_FOUND',
                        'message': 'Expense not found'
                    }
                }), 404
            return jsonify(expense)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_EXPENSE_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.delete('/<expense_id>')
    @auth_required
    def delete_expense(expense_id):
        try:
            success = expense_service.delete_expense(expense_id)
            if not success:
                return jsonify({
                    'error': {
                        'code': 'EXPENSE_NOT_FOUND',
                        'message': 'Expense not found'
                    }
                }), 404
            return jsonify({
                'message': 'Expense deleted and balances recalculated',
                'success': True
            })
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'DELETE_EXPENSE_ERROR',
                    'message': str(err)
                }
            }), 500

    return bp
