import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Bell, Home, BarChart3, Calendar, Sparkles, Settings, LogOut } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { useAnnouncementStore } from '../stores/announcementStore';

export default function Layout() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore();
  const { unreadCount } = useAnnouncementStore();
  const navigate = useNavigate();
  const isRTL = i18n.dir() === 'rtl';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-light-gray flex flex-col" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Top Header */}
      <header className="bg-white border-b border-medium-gray px-4 py-2 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center">
          <img src="/logo.png" alt="ReadySetClass" className="h-9" />
        </div>
        <div className="flex items-center gap-1">
          <span className="text-sm text-dark-gray hidden sm:inline mr-2">
            {user?.full_name || user?.email}
          </span>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `p-2 rounded-lg transition ${isActive ? 'text-student-blue bg-student-blue/10' : 'text-dark-gray hover:bg-light-gray'}`
            }
            title={t('common.settings')}
          >
            <Settings className="w-4 h-4" />
          </NavLink>
          <button
            onClick={handleLogout}
            className="p-2 hover:bg-light-gray rounded-lg transition text-dark-gray"
            title={t('common.logout')}
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 pb-20">
        <Outlet />
      </main>

      {/* Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-medium-gray safe-bottom z-20">
        <div className="flex items-center justify-around max-w-lg mx-auto">
          <NavItem to="/dashboard" icon={<Home className="w-5 h-5" />} label={t('nav.home')} />
          <NavItem
            to="/announcements"
            icon={
              <div className="relative">
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute -top-1.5 -right-1.5 bg-error text-white text-[10px] font-bold min-w-[16px] h-4 rounded-full flex items-center justify-center px-1">
                    {unreadCount > 99 ? '99+' : unreadCount}
                  </span>
                )}
              </div>
            }
            label={t('nav.alerts')}
          />
          <NavItem to="/deadlines" icon={<Calendar className="w-5 h-5" />} label={t('nav.due')} />
          <NavItem to="/grades" icon={<BarChart3 className="w-5 h-5" />} label={t('nav.grades')} />
          <NavItem to="/study" icon={<Sparkles className="w-5 h-5" />} label={t('nav.study')} />
        </div>
      </nav>
    </div>
  );
}

function NavItem({
  to,
  icon,
  label,
}: {
  to: string;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex flex-col items-center py-2 px-4 min-h-[48px] transition-colors ${
          isActive ? 'text-student-blue' : 'text-dark-gray hover:text-navy-primary'
        }`
      }
    >
      {icon}
      <span className="text-[11px] mt-0.5 font-medium">{label}</span>
    </NavLink>
  );
}
