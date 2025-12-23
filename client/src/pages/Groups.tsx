import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import type { User, Group } from '../types';
import { apiService } from '../services/api';
import CreateGroupModal from '../components/CreateGroupModal';
import CreateUserModal from '../components/CreateUserModal';

interface GroupsProps {
  currentUser: User | null;
  onUserCreated: (user: User) => void;
}

export default function Groups({ currentUser, onUserCreated }: GroupsProps) {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);

  useEffect(() => {
    loadGroups();
  }, []);

  const loadGroups = async () => {
    try {
      const fetchedGroups = await apiService.getGroups();
      setGroups(fetchedGroups);
    } catch (error) {
      console.error('Failed to load groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGroupCreated = (group: Group) => {
    setGroups([...groups, group]);
    setShowCreateModal(false);
  };

  if (!currentUser) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card p-12 text-center">
          <div className="w-20 h-20 bg-black/5 rounded-full flex items-center justify-center mx-auto mb-6 border border-black/10">
            <svg className="w-10 h-10 text-gray-800" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h2 className="text-3xl brand-title font-semibold text-gray-900 mb-4">Create an Account</h2>
          <p className="text-gray-700 mb-8 text-lg">You need an account to create and manage groups.</p>
          <button onClick={() => setShowUserModal(true)} className="btn-gradient px-6 py-3">
            Create Account
          </button>
        </div>

        {showUserModal && (
          <CreateUserModal
            onClose={() => setShowUserModal(false)}
            onUserCreated={(user) => {
              onUserCreated(user);
              setShowUserModal(false);
            }}
          />
        )}
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

  const userGroups = groups.filter(g => g.members.includes(currentUser.id));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Your Groups</h1>
          <p className="text-gray-600 mt-1">Manage and track shared expenses</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-gradient px-6 py-3 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Create Group</span>
        </button>
      </div>

      {/* Groups Grid */}
      {userGroups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {userGroups.map((group) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="card hover:shadow-lg transition-all p-6 group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="w-14 h-14 bg-black/80 border border-black/10 rounded-xl flex items-center justify-center group-hover:scale-105 transition-transform shadow-md">
                  <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
                <div className="flex items-center space-x-1 text-gray-500">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                  <span className="text-sm font-medium">{group.members.length}</span>
                </div>
              </div>
              
              <h3 className="text-xl brand-title font-semibold text-gray-900 mb-2">
                {group.name}
              </h3>
              
              <p className="text-gray-600 text-sm line-clamp-2 mb-4">
                {group.description || 'No description'}
              </p>
              
              <div className="flex items-center justify-between pt-4 border-t border-gray-100">
                <span className="text-xs text-gray-500">
                  Created {new Date(group.createdAt).toLocaleDateString()}
                </span>
                <svg className="w-5 h-5 text-gray-400 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card p-12 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 className="text-2xl font-bold text-gray-900 mb-2">No Groups Yet</h3>
          <p className="text-gray-600 mb-6">Create your first group to start tracking expenses!</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-gradient px-6 py-3"
          >
            Create Your First Group
          </button>
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && currentUser && (
        <CreateGroupModal
          currentUser={currentUser}
          onClose={() => setShowCreateModal(false)}
          onGroupCreated={handleGroupCreated}
        />
      )}
    </div>
  );
}
