import { useState, useEffect } from 'react';
import type { User, Group } from '../types';
import { apiService } from '../services/api';

interface RecordSettlementModalProps {
  group: Group;
  currentUser: User;
  onClose: () => void;
  onSettlementRecorded: () => void;
  prefilledFrom?: string;
  prefilledTo?: string;
  prefilledAmount?: number;
}

export default function RecordSettlementModal({ group, currentUser, onClose, onSettlementRecorded, prefilledFrom, prefilledTo, prefilledAmount }: RecordSettlementModalProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [from, setFrom] = useState(prefilledFrom || currentUser.id);
  const [to, setTo] = useState(prefilledTo || '');
  const [amount, setAmount] = useState(prefilledAmount ? prefilledAmount.toFixed(2) : '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isSmartSettle] = useState(!!prefilledFrom && !!prefilledTo && !!prefilledAmount);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const allUsers = await apiService.getUsers();
      const groupUsers = allUsers.filter(u => group.members.includes(u.id) && u.id !== currentUser.id);
      setUsers(groupUsers);
      if (groupUsers.length > 0) {
        setTo(groupUsers[0].id);
      }
    } catch (error) {
      console.error('Failed to load users:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await apiService.recordSettlement({
        groupId: group.id,
        fromUserId: from,
        toUserId: to,
        amount: parseFloat(amount),
      });
      onSettlementRecorded();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to record settlement');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="card max-w-md w-full p-8 transform transition-all">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="brand-title text-2xl text-neutral-900">Record Settlement</h2>
            {isSmartSettle && (
              <span className="inline-flex items-center px-2 py-1 mt-1 text-xs font-medium text-indigo-700 bg-indigo-100 rounded-full">
                <svg className="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Smart Settlement
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-neutral-500 hover:text-neutral-700 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          {isSmartSettle ? (
            <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-indigo-700 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <p className="text-sm text-indigo-900">
                  <strong>Smart Settlement:</strong> This is an optimized payment based on simplified balances to minimize transactions.
                </p>
              </div>
            </div>
          ) : (
            <div className="bg-neutral-50 border border-black/10 rounded-lg p-4">
              <div className="flex items-start space-x-2">
                <svg className="w-5 h-5 text-neutral-700 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-neutral-800">
                  Record a payment to settle up balances. This doesn't create a new expense, just tracks a payment.
                </p>
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              From (Payer)
            </label>
            <select
              value={from}
              onChange={(e) => setFrom(e.target.value)}
              className="w-full px-4 py-3 border border-black/10 rounded-lg bg-white"
            >
              <option value={currentUser.id}>{currentUser.name} (You)</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              To (Recipient)
            </label>
            <select
              value={to}
              onChange={(e) => setTo(e.target.value)}
              className="w-full px-4 py-3 border border-black/10 rounded-lg bg-white"
            >
              {users.map(user => (
                <option key={user.id} value={user.id}>{user.name}</option>
              ))}
              <option value={currentUser.id}>{currentUser.name} (You)</option>
            </select>
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

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !to}
            className="btn-gradient w-full py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Recording...' : 'Record Settlement'}
          </button>
        </form>
      </div>
    </div>
  );
}
