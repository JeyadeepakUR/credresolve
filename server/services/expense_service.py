import uuid
from db import get_db

SPLIT_TYPE_EQUAL = 'EQUAL'
SPLIT_TYPE_EXACT = 'EXACT'
SPLIT_TYPE_PERCENTAGE = 'PERCENTAGE'

def map_row_to_expense(row, splits):
    """Convert database row to expense dict"""
    if not row:
        return None
    return {
        'id': row['id'],
        'groupId': row['group_id'],
        'description': row['description'],
        'totalAmount': row['total_amount'],
        'paidBy': row['paid_by'],
        'splitType': row['split_type'],
        'splits': splits,
        'createdAt': row['created_at']
    }

def validate_expense(total_amount, split_type, splits):
    """Validate expense data"""
    errors = []
    
    if total_amount <= 0:
        errors.append('Total amount must be positive')
    if not splits or len(splits) == 0:
        errors.append('At least one participant required')
    
    if split_type == SPLIT_TYPE_EXACT:
        total = sum(s.get('amount', 0) for s in splits)
        if abs(total - total_amount) > 0.01:
            errors.append(f'Sum of exact amounts ({total}) must equal total amount ({total_amount})')
    
    if split_type == SPLIT_TYPE_PERCENTAGE:
        total = sum(s.get('percentage', 0) for s in splits)
        if abs(total - 100) > 0.01:
            errors.append(f'Sum of percentages ({total}) must equal 100%')
    
    for i, split in enumerate(splits):
        if split_type == SPLIT_TYPE_EXACT and split.get('amount', 0) < 0:
            errors.append(f'Split {i}: amount cannot be negative')
        if split_type == SPLIT_TYPE_PERCENTAGE and split.get('percentage', 0) < 0:
            errors.append(f'Split {i}: percentage cannot be negative')
    
    return {'valid': len(errors) == 0, 'errors': errors}

def calculate_splits(total_amount, split_type, splits):
    """Calculate actual amounts for each split"""
    if split_type == SPLIT_TYPE_EQUAL:
        amount_per_person = total_amount / len(splits)
        return [{'userId': s['userId'], 'amount': round(amount_per_person, 2)} for s in splits]
    elif split_type == SPLIT_TYPE_EXACT:
        return [{'userId': s['userId'], 'amount': s['amount']} for s in splits]
    elif split_type == SPLIT_TYPE_PERCENTAGE:
        return [{'userId': s['userId'], 'amount': round((s['percentage'] / 100) * total_amount, 2)} for s in splits]
    else:
        raise ValueError(f'Unknown split type: {split_type}')

class ExpenseService:
    """Service for managing expenses with SQLite persistence"""
    
    def __init__(self, group_service, user_service, balance_service):
        self.group_service = group_service
        self.user_service = user_service
        self.balance_service = balance_service
    
    def add_expense(self, expense_data):
        """Add a new expense and update balances"""
        group_id = expense_data['groupId']
        description = expense_data['description']
        total_amount = expense_data['totalAmount']
        paid_by = expense_data['paidBy']
        split_type = expense_data['splitType']
        splits = expense_data['splits']
        
        group = self.group_service.get_group(group_id)
        if not group:
            raise ValueError('Group not found')
        
        if paid_by not in group['members']:
            raise ValueError('Payer must be a group member')
        
        participant_ids = [s['userId'] for s in splits]
        member_validation = self.group_service.validate_group_members(group_id, participant_ids)
        if not member_validation['valid']:
            raise ValueError(f"Users not in group: {', '.join(member_validation['nonMembers'])}")
        
        validation = validate_expense(total_amount, split_type, splits)
        if not validation['valid']:
            raise ValueError(f"Validation failed: {', '.join(validation['errors'])}")
        
        calculated_splits = calculate_splits(total_amount, split_type, splits)
        expense_id = str(uuid.uuid4())
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Insert expense
        cursor.execute(
            'INSERT INTO expenses (id, group_id, description, total_amount, paid_by, split_type) VALUES (?, ?, ?, ?, ?, ?)',
            (expense_id, group_id, description, total_amount, paid_by, split_type)
        )
        
        # Insert splits; collect balance updates to avoid write-lock across connections
        balance_updates = []
        for split in calculated_splits:
            percentage = None
            if split_type == SPLIT_TYPE_PERCENTAGE:
                original_split = next((s for s in splits if s['userId'] == split['userId']), None)
                if original_split:
                    percentage = original_split.get('percentage')
            
            cursor.execute(
                'INSERT INTO expense_splits (expense_id, user_id, amount, percentage) VALUES (?, ?, ?, ?)',
                (expense_id, split['userId'], split['amount'], percentage)
            )
            
            if split['userId'] != paid_by:
                balance_updates.append((split['userId'], split['amount']))
        
        conn.commit()
        conn.close()

        # Apply balance updates after closing the expense transaction to prevent locking
        for user_id, amount in balance_updates:
            self.balance_service.update_balance(group_id, user_id, paid_by, amount)
        
        expense = self.get_expense(expense_id)
        balances = self.balance_service.get_group_balances(group_id)
        
        return {'expense': expense, 'balances': balances}
    
    def get_expense(self, expense_id):
        """Get expense by ID"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        cursor.execute('SELECT user_id, amount, percentage FROM expense_splits WHERE expense_id = ?', (expense_id,))
        splits = [{'userId': s['user_id'], 'amount': s['amount'], 'percentage': s['percentage']} 
                  for s in cursor.fetchall()]
        
        conn.close()
        return map_row_to_expense(row, splits)
    
    def get_group_expenses(self, group_id):
        """Get all expenses for a group"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM expenses WHERE group_id = ? ORDER BY created_at DESC', (group_id,))
        rows = cursor.fetchall()
        
        expenses = []
        for row in rows:
            cursor.execute('SELECT user_id, amount, percentage FROM expense_splits WHERE expense_id = ?', (row['id'],))
            splits = [{'userId': s['user_id'], 'amount': s['amount'], 'percentage': s['percentage']} 
                      for s in cursor.fetchall()]
            expenses.append(map_row_to_expense(row, splits))
        
        conn.close()
        return expenses
    
    def get_user_expenses(self, user_id):
        """Get all expenses where user is payer or participant"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT e.* FROM expenses e 
            LEFT JOIN expense_splits s ON e.id = s.expense_id 
            WHERE e.paid_by = ? OR s.user_id = ? 
            ORDER BY e.created_at DESC
        ''', (user_id, user_id))
        rows = cursor.fetchall()
        
        expenses = []
        for row in rows:
            cursor.execute('SELECT user_id, amount, percentage FROM expense_splits WHERE expense_id = ?', (row['id'],))
            splits = [{'userId': s['user_id'], 'amount': s['amount'], 'percentage': s['percentage']} 
                      for s in cursor.fetchall()]
            expenses.append(map_row_to_expense(row, splits))
        
        conn.close()
        return expenses
    
    def delete_expense(self, expense_id):
        """Delete expense and recalculate balances"""
        expense = self.get_expense(expense_id)
        if not expense:
            return False
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        conn.commit()
        conn.close()
        
        self.recalculate_group_balances(expense['groupId'])
        return True
    
    def recalculate_group_balances(self, group_id):
        """Recalculate all balances for a group from scratch"""
        group = self.group_service.get_group(group_id)
        if not group:
            raise ValueError('Group not found')
        
        # Clear existing balances
        self.balance_service.clear_group_balances(group_id)
        
        # Recalculate from all expenses
        expenses = self.get_group_expenses(group_id)
        for expense in expenses:
            calculated_splits = calculate_splits(
                expense['totalAmount'],
                expense['splitType'],
                expense['splits']
            )
            
            for split in calculated_splits:
                if split['userId'] != expense['paidBy']:
                    self.balance_service.update_balance(
                        group_id,
                        split['userId'],
                        expense['paidBy'],
                        split['amount']
                    )
        
        # Re-apply settlements
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM settlements WHERE group_id = ?', (group_id,))
        settlements = cursor.fetchall()
        conn.close()
        
        for settlement in settlements:
            current = self.balance_service.get_balance_between_users(
                settlement['group_id'],
                settlement['from_user_id'],
                settlement['to_user_id']
            )
            if current > 0:
                amount_to_settle = min(settlement['amount'], current)
                self.balance_service.update_balance(
                    settlement['group_id'],
                    settlement['from_user_id'],
                    settlement['to_user_id'],
                    -amount_to_settle
                )
