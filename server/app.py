import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from db import init_db
from services.user_service import UserService
from services.group_service import GroupService
from services.balance_service import BalanceService
from services.expense_service import ExpenseService
from services.settlement_service import SettlementService
from routes.auth_routes import create_auth_routes
from routes.user_routes import create_user_routes
from routes.group_routes import create_group_routes
from routes.expense_routes import create_expense_routes
from routes.settlement_routes import create_settlement_routes

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    CORS(
        app,
        resources={r"/*": {
        "origins": [
            "https://credresolve-z6n6.vercel.app", # Your production URL
            "http://localhost:3000"                  # Your local dev URL
        ]
        }},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"]
    )

    # Initialize database schema
    init_db()

    # Instantiate services
    user_service = UserService()
    balance_service = BalanceService()
    group_service = GroupService(user_service)
    expense_service = ExpenseService(group_service, user_service, balance_service)
    settlement_service = SettlementService(group_service, user_service, balance_service)

    # Register blueprints
    app.register_blueprint(create_auth_routes(user_service))
    app.register_blueprint(create_user_routes(user_service, balance_service))
    app.register_blueprint(create_group_routes(group_service, expense_service, balance_service))
    app.register_blueprint(create_expense_routes(expense_service))
    app.register_blueprint(create_settlement_routes(settlement_service))

    @app.get('/health')
    def health():
        return jsonify({
            'status': 'ok',
            'timestamp': datetime.utcnow().isoformat()
        })

    @app.get('/')
    def index():
        return jsonify({
            'message': 'CredResolve backend (Flask)',
            'routes': {
                'auth': '/api/auth',
                'users': '/api/users',
                'groups': '/api/groups',
                'expenses': '/api/expenses',
                'settlements': '/api/settlements'
            }
        })

    return app


app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=True)
