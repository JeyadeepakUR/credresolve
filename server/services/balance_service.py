from db import get_db

def map_row_to_balance(row):
    """Convert database row to balance dict"""
    if not row:
        return None
    return {
        'groupId': row['group_id'],
        'fromUserId': row['from_user_id'],
        'toUserId': row['to_user_id'],
        'amount': round(float(row['amount']), 2)
    }

class BalanceService:
    """Service for managing and calculating balances persisted in SQLite"""
    
    def __init__(self):
        pass
    
    def set_balance(self, group_id, from_user_id, to_user_id, amount):
        """Set balance (upsert pattern)"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Delete existing
        cursor.execute(
            'DELETE FROM balances WHERE group_id = ? AND from_user_id = ? AND to_user_id = ?',
            (group_id, from_user_id, to_user_id)
        )
        
        # Insert if amount > 0
        if amount > 0:
            cursor.execute(
                'INSERT INTO balances (group_id, from_user_id, to_user_id, amount) VALUES (?, ?, ?, ?)',
                (group_id, from_user_id, to_user_id, amount)
            )
        
        conn.commit()
        conn.close()
    
    def get_balance_between_users(self, group_id, from_user_id, to_user_id):
        """Get balance between two users"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT amount FROM balances WHERE group_id = ? AND from_user_id = ? AND to_user_id = ?',
            (group_id, from_user_id, to_user_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        return row['amount'] if row else 0
    
    def update_balance(self, group_id, from_user_id, to_user_id, amount):
        """Update balance with netting logic"""
        reverse = self.get_balance_between_users(group_id, to_user_id, from_user_id)
        
        if reverse > 0:
            if reverse > amount:
                new_amount = reverse - amount
                self.set_balance(group_id, to_user_id, from_user_id, new_amount)
            elif reverse < amount:
                self.set_balance(group_id, to_user_id, from_user_id, 0)
                new_amount = amount - reverse
                self.set_balance(group_id, from_user_id, to_user_id, new_amount)
            else:
                self.set_balance(group_id, to_user_id, from_user_id, 0)
        else:
            current = self.get_balance_between_users(group_id, from_user_id, to_user_id)
            new_amount = current + amount
            self.set_balance(group_id, from_user_id, to_user_id, new_amount)

    def settle_balance(self, group_id, from_user_id, to_user_id, amount):
        """Settle an existing balance between two users"""
        current = self.get_balance_between_users(group_id, from_user_id, to_user_id)
        if current == 0:
            raise ValueError('No balance exists between these users')
        if amount > current + 0.01:
            raise ValueError(f'Settlement amount ({amount}) exceeds current balance ({current})')
        new_balance = current - amount
        self.set_balance(group_id, from_user_id, to_user_id, new_balance)
    
    def get_group_balances(self, group_id):
        """Get all balances for a group"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM balances WHERE group_id = ?', (group_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [map_row_to_balance(row) for row in rows if row['amount'] > 0]
    
    def get_user_balances_in_group(self, group_id, user_id):
        """Get user's balances within a specific group"""
        all_balances = self.get_group_balances(group_id)
        owes = [b for b in all_balances if b['fromUserId'] == user_id]
        owed = [b for b in all_balances if b['toUserId'] == user_id]
        return {'owes': owes, 'owed': owed}
    
    def get_user_balances(self, user_id):
        """Get all balances for a user across all groups"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM balances WHERE from_user_id = ? OR to_user_id = ?',
            (user_id, user_id)
        )
        rows = cursor.fetchall()
        conn.close()
        
        balances = [map_row_to_balance(row) for row in rows]
        owes = [b for b in balances if b['fromUserId'] == user_id]
        owed = [b for b in balances if b['toUserId'] == user_id]
        
        total_owes = sum(b['amount'] for b in owes)
        total_owed = sum(b['amount'] for b in owed)
        net_balance = round(total_owed - total_owes, 2)
        
        return {
            'userId': user_id,
            'owes': owes,
            'owed': owed,
            'netBalance': net_balance
        }
    
    def get_simplified_balances(self, group_id):
        """Get simplified balances (minimum transactions)"""
        balances = self.get_group_balances(group_id)
        
        # Build net balances per user
        net = {}
        for b in balances:
            from_user = b['fromUserId']
            to_user = b['toUserId']
            amount = b['amount']
            
            net[from_user] = net.get(from_user, 0) - amount
            net[to_user] = net.get(to_user, 0) + amount
        
        # Separate debtors and creditors
        debtors = [(user, -amt) for user, amt in net.items() if amt < -0.01]
        creditors = [(user, amt) for user, amt in net.items() if amt > 0.01]
        
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)
        
        simplified = []
        i, j = 0, 0
        
        while i < len(debtors) and j < len(creditors):
            debtor, debt = debtors[i]
            creditor, credit = creditors[j]
            
            amount = min(debt, credit)
            simplified.append({
                'groupId': group_id,
                'fromUserId': debtor,
                'toUserId': creditor,
                'amount': round(amount, 2)
            })
            
            debtors[i] = (debtor, debt - amount)
            creditors[j] = (creditor, credit - amount)
            
            if debtors[i][1] < 0.01:
                i += 1
            if creditors[j][1] < 0.01:
                j += 1
        
        return simplified
    
    def clear_group_balances(self, group_id):
        """Clear all balances for a group"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM balances WHERE group_id = ?', (group_id,))
        conn.commit()
        conn.close()
    
    def apply_smart_settlement(self, group_id, payer_id, recipient_id, amount):
        """Apply a smart settlement by reducing payer's debts and recipient's credits proportionally"""
        all_balances = self.get_group_balances(group_id)
        
        # Find all debts where payer owes money
        payer_debts = [b for b in all_balances if b['fromUserId'] == payer_id]
        total_payer_debt = sum(b['amount'] for b in payer_debts)
        
        # Find all credits where recipient is owed money
        recipient_credits = [b for b in all_balances if b['toUserId'] == recipient_id]
        total_recipient_credit = sum(b['amount'] for b in recipient_credits)
        
        remaining_amount = amount
        
        # Reduce payer's debts proportionally
        if total_payer_debt > 0:
            for debt in payer_debts:
                if remaining_amount <= 0:
                    break
                reduction = min(debt['amount'], remaining_amount)
                new_balance = debt['amount'] - reduction
                self.set_balance(group_id, debt['fromUserId'], debt['toUserId'], new_balance)
                remaining_amount -= reduction
        
        # Reset remaining amount for recipient side
        remaining_amount = amount
        
        # Reduce recipient's credits proportionally
        if total_recipient_credit > 0:
            for credit in recipient_credits:
                if remaining_amount <= 0:
                    break
                reduction = min(credit['amount'], remaining_amount)
                new_balance = credit['amount'] - reduction
                self.set_balance(group_id, credit['fromUserId'], credit['toUserId'], new_balance)
                remaining_amount -= reduction
