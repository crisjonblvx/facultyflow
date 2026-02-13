import { useEffect } from 'react';
import { Settings, Link2, LogOut, Globe, Sparkles, CreditCard } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuthStore } from '../stores/authStore';
import { useSubscriptionStore } from '../stores/subscriptionStore';
import { LANGUAGES } from '../i18n';

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuthStore();
  const { subscription, fetchStatus, cancelSubscription } = useSubscriptionStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const upgraded = searchParams.get('upgraded') === 'true';

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const changeLanguage = (code: string) => {
    i18n.changeLanguage(code);
    document.documentElement.dir = code === 'ar' ? 'rtl' : 'ltr';
  };

  const handleCancel = async () => {
    if (!confirm(t('settings.cancelConfirm'))) return;
    try {
      await cancelSubscription();
      fetchStatus();
    } catch {
      alert(t('common.error'));
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2 mb-6">
        <Settings className="w-5 h-5" />
        {t('settings.title')}
      </h1>

      {/* Upgrade Success Banner */}
      {upgraded && (
        <div className="bg-success/10 border border-success/30 rounded-xl p-4 mb-4 text-center">
          <Sparkles className="w-6 h-6 text-success mx-auto mb-1" />
          <p className="font-semibold text-success">{t('settings.upgradeSuccess')}</p>
        </div>
      )}

      {/* Subscription Status */}
      <div className="bg-white rounded-xl shadow-md p-5 mb-4">
        <h2 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
          <CreditCard className="w-4 h-4 text-student-blue" />
          {t('settings.subscription')}
        </h2>
        {subscription ? (
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                  subscription.has_pro
                    ? 'bg-student-blue/10 text-student-blue'
                    : 'bg-medium-gray/30 text-dark-gray'
                }`}>
                  {subscription.has_pro ? t('pricing.pro') : t('pricing.free')}
                </span>
                <span className="text-sm text-dark-gray capitalize">{subscription.status}</span>
              </div>
            </div>

            {!subscription.has_pro && (
              <div className="space-y-3">
                <div className="text-sm text-dark-gray">
                  {t('settings.aiUsage', {
                    used: subscription.ai_generations_used,
                    limit: subscription.ai_generations_limit,
                  })}
                </div>
                <button
                  onClick={() => navigate('/pricing')}
                  className="w-full bg-student-blue text-white py-2.5 rounded-lg font-semibold text-sm hover:bg-student-blue/90 transition flex items-center justify-center gap-2"
                >
                  <Sparkles className="w-4 h-4" />
                  {t('settings.upgradeToPro')}
                </button>
              </div>
            )}

            {subscription.has_pro && (
              <div className="space-y-2">
                <p className="text-sm text-dark-gray">{t('settings.proActive')}</p>
                <button
                  onClick={handleCancel}
                  className="text-sm text-error hover:underline"
                >
                  {t('settings.cancelSubscription')}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="animate-pulse h-16 bg-light-gray rounded-lg" />
        )}
      </div>

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
