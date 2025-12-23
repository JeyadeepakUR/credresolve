from flask import Blueprint, request, jsonify
from middleware.auth import auth_required

def create_settlement_routes(settlement_service):
    bp = Blueprint('settlement_routes', __name__, url_prefix='/api/settlements')

    @bp.post('/')
    @auth_required
    def record_settlement():
        data = request.get_json() or {}
        group_id = data.get('groupId')
        from_user_id = data.get('fromUserId') or getattr(request, 'user', {}).get('id')
        to_user_id = data.get('toUserId')
        amount = data.get('amount')

        if not group_id or not from_user_id or not to_user_id or amount is None:
            return jsonify({
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'All fields are required: groupId, fromUserId, toUserId, amount'
                }
            }), 400

        try:
            result = settlement_service.record_settlement({
                'groupId': group_id,
                'fromUserId': from_user_id,
                'toUserId': to_user_id,
                'amount': amount
            })
            return jsonify({
                'settlement': result['settlement'],
                'remainingBalance': result['remainingBalance']
            }), 201
        except ValueError as err:
            return jsonify({
                'error': {
                    'code': 'RECORD_SETTLEMENT_ERROR',
                    'message': str(err)
                }
            }), 400
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'RECORD_SETTLEMENT_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/<settlement_id>')
    @auth_required
    def get_settlement(settlement_id):
        try:
            settlement = settlement_service.get_settlement(settlement_id)
            if not settlement:
                return jsonify({
                    'error': {
                        'code': 'SETTLEMENT_NOT_FOUND',
                        'message': 'Settlement not found'
                    }
                }), 404
            return jsonify(settlement)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_SETTLEMENT_ERROR',
                    'message': str(err)
                }
            }), 500

    @bp.get('/groups/<group_id>')
    @auth_required
    def get_group_settlements(group_id):
        try:
            settlements = settlement_service.get_group_settlements(group_id)
            return jsonify(settlements)
        except Exception as err:
            return jsonify({
                'error': {
                    'code': 'GET_SETTLEMENTS_ERROR',
                    'message': str(err)
                }
            }), 500

    return bp
