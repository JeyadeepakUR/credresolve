import { useState, useEffect } from 'react';
import type { User, Group } from '../types';
import { apiService } from '../services/api';

interface AddExpenseModalProps {
  group: Group;
  currentUser: User;
  onClose: () => void;
  onExpenseAdded: () => void;
}

export default function AddExpenseModal({ group, currentUser, onClose, onExpenseAdded }: AddExpenseModalProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState('');
  const [paidBy, setPaidBy] = useState(currentUser.id);
  const [splitType, setSplitType] = useState<'EQUAL' | 'EXACT' | 'PERCENTAGE'>('EQUAL');
  const [splits, setSplits] = useState<{ userId: string; amount?: number; percentage?: number }[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const allUsers = await apiService.getUsers();
      const groupUsers = allUsers.filter(u => group.members.includes(u.id));
      setUsers(groupUsers);
      
      // Initialize splits for all members
      setSplits(groupUsers.map(u => ({ userId: u.id })));
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const expenseData: any = {
        groupId: group.id,
        description,
        totalAmount: parseFloat(amount),
        paidBy,
        splitType,
        splits: []
      };

      if (splitType === 'EQUAL') {
        // For equal split, include all group members
        expenseData.splits = users.map(u => ({ userId: u.id }));
      } else if (splitType === 'EXACT') {
        expenseData.splits = splits
          .filter(s => s.amount && s.amount > 0)
          .map(s => ({ userId: s.userId, amount: s.amount! }));
      } else if (splitType === 'PERCENTAGE') {
        expenseData.splits = splits
          .filter(s => s.percentage && s.percentage > 0)
          .map(s => ({ userId: s.userId, percentage: s.percentage! }));
      }

      await apiService.addExpense(expenseData);
      onExpenseAdded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add expense');
    } finally {
      setLoading(false);
    }
  };

  const updateSplit = (userId: string, field: 'amount' | 'percentage', value: string) => {
    setSplits(splits.map(s => 
      s.userId === userId 
        ? { ...s, [field]: value ? parseFloat(value) : undefined }
        : s
    ));
  };

  const totalSplitAmount = splits.reduce((sum, s) => sum + (s.amount || 0), 0);
  const totalSplitPercentage = splits.reduce((sum, s) => sum + (s.percentage || 0), 0);

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="card max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-transparent p-6 rounded-t-2xl">
          <div className="flex justify-between items-center">
            <h2 className="brand-title text-2xl text-neutral-900">Add Expense</h2>
            <button
              onClick={onClose}
              className="text-neutral-500 hover:text-neutral-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              className="w-full px-4 py-3 border border-black/10 rounded-lg bg-white"
              placeholder="e.g., Dinner at restaurant"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount ($)
            </label>
            <input
              type="number"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              required
              className="w-full px-4 py-3 border border-black/10 rounded-lg bg-white"
              placeholder="0.00"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Paid by
            </label>
            <select
              value={paidBy}
              onChange={(e) => setPaidBy(e.target.value)}
              className="w-full px-4 py-3 border border-black/10 rounded-lg bg-white"
            >
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Split Type
            </label>
            <div className="grid grid-cols-3 gap-3">
              {(['EQUAL', 'EXACT', 'PERCENTAGE'] as const).map(type => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSplitType(type)}
                  className={`py-3 px-4 rounded-lg font-medium transition-all ${
                    splitType === type
                      ? 'btn-gradient text-white'
                      : 'bg-white border border-black/10 text-neutral-700 hover:bg-neutral-100'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Split Details for EXACT */}
          {splitType === 'EXACT' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Exact Amounts
              </label>
              <div className="space-y-2 bg-neutral-50 border border-black/10 rounded-lg p-4">
                {users.map(user => (
                  <div key={user.id} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{user.name}</span>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="0.00"
                      onChange={(e) => updateSplit(user.id, 'amount', e.target.value)}
                      className="w-32 px-3 py-2 border border-black/10 rounded-lg text-sm bg-white"
                    />
                  </div>
                ))}
                <div className="pt-2 border-t border-black/10 flex items-center justify-between text-sm">
                  <span className="font-bold text-gray-900">Total:</span>
                  <span className={`font-bold ${
                    Math.abs(totalSplitAmount - parseFloat(amount || '0')) < 0.01
                      ? 'text-emerald-600'
                      : 'text-rose-600'
                  }`}>
                    ${totalSplitAmount.toFixed(2)} / ${parseFloat(amount || '0').toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Split Details for PERCENTAGE */}
          {splitType === 'PERCENTAGE' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Percentage Split
              </label>
              <div className="space-y-2 bg-neutral-50 border border-black/10 rounded-lg p-4">
                {users.map(user => (
                  <div key={user.id} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">{user.name}</span>
                    <div className="flex items-center space-x-2">
                      <input
                        type="number"
                        step="0.01"
                        placeholder="0"
                        onChange={(e) => updateSplit(user.id, 'percentage', e.target.value)}
                        className="w-24 px-3 py-2 border border-black/10 rounded-lg text-sm bg-white"
                      />
                      <span className="text-sm text-gray-500">%</span>
                    </div>
                  </div>
                ))}
                <div className="pt-2 border-t border-black/10 flex items-center justify-between text-sm">
                  <span className="font-bold text-gray-900">Total:</span>
                  <span className={`font-bold ${
                    Math.abs(totalSplitPercentage - 100) < 0.01
                      ? 'text-emerald-600'
                      : 'text-rose-600'
                  }`}>
                    {totalSplitPercentage.toFixed(2)}% / 100%
                  </span>
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-gradient w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Adding...' : 'Add Expense'}
          </button>
        </form>
      </div>
    </div>
  );
}
