import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Groups from './pages/Groups';
import GroupDetail from './pages/GroupDetail';
import type { User } from './types';
import { apiService } from './services/api';

function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const bootstrap = async () => {
      try {
        // Check if we have a token in sessionStorage
        const token = sessionStorage.getItem('token');
        
        if (token) {
          // If token exists, verify it and get current user
          try {
            const me = await apiService.me();
            setCurrentUser(me);
          } catch (error) {
            // Token is invalid, clear it
            apiService.clearToken();
          }
        }
      } catch (e) {
        console.error('Bootstrap error:', e);
      } finally {
        setLoading(false);
      }
    };
    bootstrap();
  }, []);

  const handleUserCreated = (user: User) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    apiService.clearToken();
    setCurrentUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Layout 
        currentUser={currentUser} 
        onUserCreated={handleUserCreated}
        onLogout={handleLogout}
      >
        <Routes>
          <Route path="/" element={<Dashboard currentUser={currentUser} />} />
          <Route path="/groups" element={<Groups currentUser={currentUser} onUserCreated={handleUserCreated} />} />
          <Route path="/groups/:groupId" element={<GroupDetail currentUser={currentUser} />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
