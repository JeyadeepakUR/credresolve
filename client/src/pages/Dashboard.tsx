import { useEffect, useState } from 'react';
import type { User, UserBalance } from '../types';
import { apiService } from '../services/api';

interface DashboardProps {
  currentUser: User | null;
}

export default function Dashboard({ currentUser }: DashboardProps) {
  const [balances, setBalances] = useState<UserBalance | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentUser) {
      loadData();
    } else {
      setLoading(false);
    }
  }, [currentUser]);

  const loadData = async () => {
    if (!currentUser) return;

    try {
      const [userBalances, allUsers] = await Promise.all([
        apiService.getUserBalances(currentUser.id),
        apiService.getUsers(),
      ]);
      setBalances(userBalances);
      setUsers(allUsers);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getUserName = (userId: string) => {
    return users.find(u => u.id === userId)?.name || 'Unknown';
  };

  if (!currentUser) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <div className="w-20 h-20 bg-black/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-black/10">
            <svg className="w-10 h-10 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-3xl brand-title font-semibold text-gray-900 mb-4">Welcome to CredResolve</h2>
          <p className="text-gray-700 mb-8 text-lg">Create an account to start tracking and splitting expenses with friends.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  const totalOwes = balances?.owes.reduce((sum, b) => sum + b.amount, 0) || 0;
  const totalOwed = balances?.owed.reduce((sum, b) => sum + b.amount, 0) || 0;
  const netBalance = balances?.netBalance || 0;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="card p-8">
        <h1 className="text-3xl brand-title font-semibold text-gray-900 mb-2">Welcome back, {currentUser.name}</h1>
        <p className="text-gray-600">Here's your expense overview</p>
      </div>

      {/* Balance Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* You Owe */}
        <div className="card p-6 border-l-4 border-rose-400">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-rose-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-500">You Owe</span>
          </div>
          <p className="text-3xl brand-title font-semibold text-rose-600">${totalOwes.toFixed(2)}</p>
          <p className="text-sm text-gray-600 mt-2">{balances?.owes.length || 0} people</p>
        </div>

        {/* You Are Owed */}
        <div className="card p-6 border-l-4 border-emerald-400">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 13l-5 5m0 0l-5-5m5 5V6" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-500">You're Owed</span>
          </div>
          <p className="text-3xl brand-title font-semibold text-emerald-600">${totalOwed.toFixed(2)}</p>
          <p className="text-sm text-gray-600 mt-2">{balances?.owed.length || 0} people</p>
        </div>

        {/* Net Balance */}
        <div className={`card p-6 border-l-4 ${netBalance >= 0 ? 'border-indigo-400' : 'border-amber-400'}`}>
          <div className="flex items-center justify-between mb-4">
            <div className={`w-12 h-12 ${netBalance >= 0 ? 'bg-indigo-100' : 'bg-amber-100'} rounded-lg flex items-center justify-center`}>
              <svg className={`w-6 h-6 ${netBalance >= 0 ? 'text-indigo-600' : 'text-amber-600'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="text-sm font-medium text-gray-500">Net Balance</span>
          </div>
          <p className={`text-3xl brand-title font-semibold ${netBalance >= 0 ? 'text-indigo-600' : 'text-amber-600'}`}>
            ${Math.abs(netBalance).toFixed(2)}
          </p>
          <p className="text-sm text-gray-600 mt-2">
            {netBalance > 0 ? 'You are owed' : netBalance < 0 ? 'You owe' : 'All settled up!'}
          </p>
        </div>
      </div>

      {/* Detailed Balances */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* You Owe List */}
        <div className="card overflow-hidden">
          <div className="bg-gradient-to-r from-rose-50 to-pink-50 px-6 py-4 border-b border-rose-100">
            <h3 className="text-lg font-semibold text-gray-900">You Owe</h3>
          </div>
          <div className="p-6">
            {balances && balances.owes.length > 0 ? (
              <div className="space-y-4">
                {balances.owes.map((balance, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-bone-100/50 rounded-lg border border-black/5">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-rose-400 to-pink-500 rounded-full flex items-center justify-center text-white font-semibold">
                        {getUserName(balance.toUserId).charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 brand-title">{getUserName(balance.toUserId)}</p>
                        <p className="text-sm text-gray-500">You owe</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl brand-title font-semibold text-rose-600">${balance.amount.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p className="text-gray-500">You don't owe anyone!</p>
              </div>
            )}
          </div>
        </div>

        {/* You Are Owed List */}
        <div className="card overflow-hidden">
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 px-6 py-4 border-b border-emerald-100">
            <h3 className="text-lg font-semibold text-gray-900">You're Owed</h3>
          </div>
          <div className="p-6">
            {balances && balances.owed.length > 0 ? (
              <div className="space-y-4">
                {balances.owed.map((balance, index) => (
                  <div key={index} className="flex items-center justify-between p-4 bg-bone-100/50 rounded-lg border border-black/5">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center text-white font-semibold">
                        {getUserName(balance.fromUserId).charAt(0)}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 brand-title">{getUserName(balance.fromUserId)}</p>
                        <p className="text-sm text-gray-500">Owes you</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl brand-title font-semibold text-emerald-600">${balance.amount.toFixed(2)}</p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <p className="text-gray-500">Nobody owes you!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
