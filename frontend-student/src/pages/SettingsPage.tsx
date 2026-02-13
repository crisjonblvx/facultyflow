import { Settings, Link2, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';

export default function SettingsPage() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2 mb-6">
        <Settings className="w-5 h-5" />
        Settings
      </h1>

      {/* Profile */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3">Profile</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-dark-gray">Name</span>
            <span className="font-medium">{user?.full_name || '-'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-gray">Email</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-gray">Account Type</span>
            <span className="font-medium capitalize">{user?.role}</span>
          </div>
        </div>
      </div>

      {/* Canvas Connection */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3">Canvas Connection</h2>
        <button
          onClick={() => navigate('/setup')}
          className="w-full flex items-center gap-3 px-4 py-3 border border-medium-gray rounded-lg hover:bg-light-gray transition"
        >
          <Link2 className="w-5 h-5 text-student-blue" />
          <span className="text-sm font-medium">Reconnect Canvas</span>
        </button>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full bg-white rounded-xl shadow-md p-4 flex items-center gap-3 hover:bg-light-gray transition text-error font-semibold"
      >
        <LogOut className="w-5 h-5" />
        Sign Out
      </button>

      <p className="text-center text-xs text-dark-gray mt-8">
        ReadySetClass Student Edition v1.0
      </p>
    </div>
  );
}
