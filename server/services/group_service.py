import uuid
from db import get_db

def map_row_to_group(row, members=None):
    """Convert database row to group dict"""
    if not row:
        return None
    if members is None:
        members = []
    return {
        'id': row['id'],
        'name': row['name'],
        'description': row['description'],
        'members': members,
        'createdBy': row['created_by'],
        'createdAt': row['created_at']
    }

class GroupService:
    """Service for managing groups with SQLite persistence"""
    
    def __init__(self, user_service):
        self.user_service = user_service
    
    def create_group(self, name, description, created_by):
        """Create a new group and add creator as member"""
        if not self.user_service.user_exists(created_by):
            raise ValueError('Creator user does not exist')
        
        conn = get_db()
        cursor = conn.cursor()
        
        group_id = str(uuid.uuid4())
        
        # Create group
        cursor.execute(
            'INSERT INTO groups (id, name, description, created_by) VALUES (?, ?, ?, ?)',
            (group_id, name, description, created_by)
        )
        
        # Add creator as member
        cursor.execute(
            'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
            (group_id, created_by)
        )
        
        conn.commit()
        conn.close()
        
        return self.get_group(group_id)
    
    def get_group(self, group_id):
        """Get group by ID with members"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groups WHERE id = ?', (group_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return None
        
        cursor.execute('SELECT user_id FROM group_members WHERE group_id = ?', (group_id,))
        members = [m['user_id'] for m in cursor.fetchall()]
        
        conn.close()
        return map_row_to_group(row, members)
    
    def get_all_groups(self):
        """Get all groups"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM groups ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        groups = []
        for row in rows:
            cursor.execute('SELECT user_id FROM group_members WHERE group_id = ?', (row['id'],))
            members = [m['user_id'] for m in cursor.fetchall()]
            groups.append(map_row_to_group(row, members))
        
        conn.close()
        return groups
    
    def get_user_groups(self, user_id):
        """Get all groups user is a member of"""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT g.* FROM groups g 
            JOIN group_members gm ON g.id = gm.group_id 
            WHERE gm.user_id = ? 
            ORDER BY g.created_at DESC
        ''', (user_id,))
        rows = cursor.fetchall()
        
        groups = []
        for row in rows:
            cursor.execute('SELECT user_id FROM group_members WHERE group_id = ?', (row['id'],))
            members = [m['user_id'] for m in cursor.fetchall()]
            groups.append(map_row_to_group(row, members))
        
        conn.close()
        return groups
    
    def add_member(self, group_id, user_id):
        """Add a member to a group"""
        group = self.get_group(group_id)
        if not group:
            raise ValueError('Group not found')
        
        if not self.user_service.user_exists(user_id):
            raise ValueError('User does not exist')
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if already a member
        cursor.execute(
            'SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?',
            (group_id, user_id)
        )
        if cursor.fetchone():
            conn.close()
            return False
        
        cursor.execute(
            'INSERT INTO group_members (group_id, user_id) VALUES (?, ?)',
            (group_id, user_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def group_exists(self, group_id):
        """Check if group exists"""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM groups WHERE id = ?', (group_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def validate_group_members(self, group_id, user_ids):
        """Validate that all users are members of the group"""
        group = self.get_group(group_id)
        if not group:
            return {'valid': False, 'nonMembers': user_ids}
        
        conn = get_db()
        cursor = conn.cursor()
        
        non_members = []
        for user_id in user_ids:
            cursor.execute(
                'SELECT 1 FROM group_members WHERE group_id = ? AND user_id = ?',
                (group_id, user_id)
            )
            if not cursor.fetchone():
                non_members.append(user_id)
        
        conn.close()
        return {
            'valid': len(non_members) == 0,
            'nonMembers': non_members
        }
