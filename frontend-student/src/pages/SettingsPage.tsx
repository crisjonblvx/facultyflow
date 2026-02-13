import { Settings, Link2, LogOut, Globe } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { LANGUAGES } from '../i18n';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const changeLanguage = (code: string) => {
    i18n.changeLanguage(code);
    document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2 mb-6">
        <Settings className="w-5 h-5" />
        {t('settings.title')}
      </h1>

      {/* Profile */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3">{t('settings.profile')}</h2>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className="text-dark-gray">{t('settings.name')}</span>
            <span className="font-medium">{user?.full_name || '-'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-gray">{t('settings.email')}</span>
            <span className="font-medium">{user?.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-dark-gray">{t('settings.accountType')}</span>
            <span className="font-medium capitalize">{user?.role}</span>
          </div>
        </div>
      </div>

      {/* Language */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
          <Globe className="w-4 h-4 text-student-blue" />
          {t('settings.language')}
        </h2>
        <div className="grid grid-cols-2 gap-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={`px-3 py-2.5 rounded-lg border-2 text-left text-sm transition ${
                i18n.language === lang.code || i18n.language.startsWith(lang.code + '-')
                  ? 'border-student-blue bg-student-blue/5 text-student-blue font-semibold'
                  : 'border-medium-gray text-dark-gray hover:border-student-blue/50'
              }`}
            >
              <span className="block font-medium">{lang.nativeName}</span>
              <span className="text-[11px] opacity-60">{lang.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Canvas Connection */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3">{t('settings.canvasConnection')}</h2>
        <button
          onClick={() => navigate('/setup')}
          className="w-full flex items-center gap-3 px-4 py-3 border border-medium-gray rounded-lg hover:bg-light-gray transition"
        >
          <Link2 className="w-5 h-5 text-student-blue" />
          <span className="text-sm font-medium">{t('settings.reconnect')}</span>
        </button>
      </div>

      {/* Logout */}
      <button
        onClick={handleLogout}
        className="w-full bg-white rounded-xl shadow-md p-4 flex items-center gap-3 hover:bg-light-gray transition text-error font-semibold"
      >
        <LogOut className="w-5 h-5" />
        {t('settings.signOut')}
      </button>

      <p className="text-center text-xs text-dark-gray mt-8">
        {t('settings.version')}
      </p>
    </div>
  );
}
