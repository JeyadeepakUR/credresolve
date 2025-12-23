from uuid import uuid4
from db import get_db

def map_row_to_settlement(row):
    """Convert database row to settlement dict"""
    if not row:
        return None
    return {
        'id': row['id'],
        'groupId': row['group_id'],
        'fromUserId': row['from_user_id'],
        'toUserId': row['to_user_id'],
        'amount': row['amount'],
        'settledAt': row['settled_at']
    }

class SettlementService:
    """Service for managing settlements with SQLite persistence"""
    
    def __init__(self, group_service, user_service, balance_service):
        self.group_service = group_service
        self.user_service = user_service
        self.balance_service = balance_service
    
    def record_settlement(self, settlement_data):
        """
        Record a settlement between two users in a group
        
        Args:
            settlement_data: Dict with groupId, fromUserId, toUserId, amount
            
        Returns:
            Dict with settlement and remainingBalance
            
        Raises:
            ValueError: If validation fails
        """
        group_id = settlement_data.get('groupId')
        from_user_id = settlement_data.get('fromUserId')
        to_user_id = settlement_data.get('toUserId')
        amount = settlement_data.get('amount')
        
        # Validate group exists
        group = self.group_service.get_group(group_id)
        if not group:
            raise ValueError('Group not found')
        
        # Validate both users are members
        # group['members'] is a list of user IDs (strings)
        member_ids = group['members']
        if from_user_id not in member_ids or to_user_id not in member_ids:
            raise ValueError('Both users must be group members')
        
        # Validate amount
        if amount <= 0:
            raise ValueError('Settlement amount must be positive')
        
        # Get all group balances to calculate net positions
        all_balances = self.balance_service.get_group_balances(group_id)
        
        # Calculate net balance for from_user (should be negative = owes money)
        from_user_net = 0
        for b in all_balances:
            if b['fromUserId'] == from_user_id:
                from_user_net -= b['amount']
            elif b['toUserId'] == from_user_id:
                from_user_net += b['amount']
        
        # Calculate net balance for to_user (should be positive = owed money)
        to_user_net = 0
        for b in all_balances:
            if b['fromUserId'] == to_user_id:
                to_user_net -= b['amount']
            elif b['toUserId'] == to_user_id:
                to_user_net += b['amount']
        
        # Smart settlement validation: from_user should owe money overall, to_user should be owed
        if from_user_net >= 0:
            raise ValueError(f'{from_user_id} does not owe money in this group')
        if to_user_net <= 0:
            raise ValueError(f'{to_user_id} is not owed money in this group')
        
        # Amount should not exceed what from_user owes OR what to_user is owed
        max_from = abs(from_user_net)
        max_to = abs(to_user_net)
        max_allowed = min(max_from, max_to)
        
        if amount > max_allowed + 0.01:
            raise ValueError(
                f'Settlement amount ({amount}) exceeds maximum allowed ({max_allowed:.2f})'
            )
        
        # Create settlement
        settlement_id = str(uuid4())
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            '''INSERT INTO settlements (id, group_id, from_user_id, to_user_id, amount)
               VALUES (?, ?, ?, ?, ?)''',
            (settlement_id, group_id, from_user_id, to_user_id, amount)
        )
        conn.commit()
        conn.close()

        # Apply smart settlement: reduce payer's debts and recipient's credits
        self.balance_service.apply_smart_settlement(group_id, from_user_id, to_user_id, amount)
        
        # Get created settlement
        settlement = self.get_settlement(settlement_id)
        
        # Calculate remaining net balance for from_user
        updated_balances = self.balance_service.get_group_balances(group_id)
        remaining_balance = 0
        for b in updated_balances:
            if b['fromUserId'] == from_user_id:
                remaining_balance -= b['amount']
            elif b['toUserId'] == from_user_id:
                remaining_balance += b['amount']
        
        return {
            'settlement': settlement,
            'remainingBalance': round(remaining_balance, 2)
        }
    
    def get_settlement(self, settlement_id):
        """Get settlement by ID"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM settlements WHERE id = ?', (settlement_id,))
        row = cursor.fetchone()
        conn.close()

        return map_row_to_settlement(row)
    
    def get_group_settlements(self, group_id):
        """Get all settlements for a group"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM settlements WHERE group_id = ? ORDER BY settled_at DESC',
            (group_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [map_row_to_settlement(row) for row in rows if row]
    
    def get_user_settlements(self, user_id):
        """Get all settlements involving a user"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            '''SELECT * FROM settlements 
               WHERE from_user_id = ? OR to_user_id = ? 
               ORDER BY settled_at DESC''',
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        conn.close()

        return [map_row_to_settlement(row) for row in rows if row]
