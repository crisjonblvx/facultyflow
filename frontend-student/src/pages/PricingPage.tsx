import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Check, Sparkles, BookOpen, Brain, PenTool, CalendarClock, Shield, Zap } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useSubscriptionStore } from '../stores/subscriptionStore';

const STUDENT_PRO_MONTHLY_PRICE_ID = import.meta.env.VITE_STRIPE_STUDENT_PRO_MONTHLY || '';
const STUDENT_PRO_YEARLY_PRICE_ID = import.meta.env.VITE_STRIPE_STUDENT_PRO_YEARLY || '';

export default function PricingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { subscription, fetchStatus, createCheckout } = useSubscriptionStore();
  const [billing, setBilling] = useState<'monthly' | 'yearly'>('monthly');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleUpgrade = async () => {
    const priceId = billing === 'monthly' ? STUDENT_PRO_MONTHLY_PRICE_ID : STUDENT_PRO_YEARLY_PRICE_ID;
    if (!priceId) {
      alert('Stripe is not configured yet. Please contact support.');
      return;
    }
    setLoading(true);
    try {
      const checkoutUrl = await createCheckout(priceId, 'pro');
      window.location.href = checkoutUrl;
    } catch {
      alert('Failed to start checkout. Please try again.');
      setLoading(false);
    }
  };

  if (subscription?.has_pro) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-10 text-center">
        <div className="bg-white rounded-2xl shadow-md p-8">
          <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="w-8 h-8 text-success" />
          </div>
          <h1 className="text-2xl font-bold text-navy-primary mb-2">{t('pricing.alreadyPro')}</h1>
          <p className="text-dark-gray mb-6">{t('pricing.alreadyProDesc')}</p>
          <button
            onClick={() => navigate('/study')}
            className="bg-student-blue text-white px-6 py-3 rounded-xl font-semibold hover:bg-student-blue/90 transition"
          >
            {t('pricing.goToStudyTools')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-navy-primary mb-1">{t('pricing.title')}</h1>
        <p className="text-dark-gray text-sm">{t('pricing.subtitle')}</p>
      </div>

      {/* Billing Toggle */}
      <div className="flex items-center justify-center gap-2 mb-6">
        <button
          onClick={() => setBilling('monthly')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            billing === 'monthly'
              ? 'bg-student-blue text-white'
              : 'bg-white text-dark-gray border border-medium-gray'
          }`}
        >
          {t('pricing.monthly')}
        </button>
        <button
          onClick={() => setBilling('yearly')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            billing === 'yearly'
              ? 'bg-student-blue text-white'
              : 'bg-white text-dark-gray border border-medium-gray'
          }`}
        >
          {t('pricing.yearly')}
          <span className="ml-1 text-xs opacity-80">{t('pricing.savePercent')}</span>
        </button>
      </div>

      {/* Plans Grid */}
      <div className="space-y-4">
        {/* Free Plan */}
        <div className="bg-white rounded-xl shadow-sm border-2 border-medium-gray p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-text-primary">{t('pricing.free')}</h2>
              <p className="text-2xl font-bold text-text-primary">$0<span className="text-sm font-normal text-dark-gray">{t('pricing.perMonth')}</span></p>
            </div>
            <div className="bg-medium-gray/30 text-dark-gray px-3 py-1 rounded-full text-xs font-medium">
              {t('pricing.currentPlan')}
            </div>
          </div>
          <ul className="space-y-2.5">
            <PlanFeature icon={<BookOpen className="w-4 h-4" />} text={t('pricing.freeFeature1')} />
            <PlanFeature icon={<Shield className="w-4 h-4" />} text={t('pricing.freeFeature2')} />
            <PlanFeature icon={<Zap className="w-4 h-4" />} text={t('pricing.freeFeature3')} />
          </ul>
        </div>

        {/* Pro Plan */}
        <div className="bg-white rounded-xl shadow-md border-2 border-student-blue p-5 relative">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold-accent text-white text-xs font-bold px-3 py-1 rounded-full">
            {t('pricing.recommended')}
          </div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-student-blue flex items-center gap-1.5">
                <Sparkles className="w-5 h-5" />
                {t('pricing.pro')}
              </h2>
              <p className="text-2xl font-bold text-text-primary">
                {billing === 'monthly' ? '$4.99' : '$49.99'}
                <span className="text-sm font-normal text-dark-gray">
                  {billing === 'monthly' ? t('pricing.perMonth') : t('pricing.perYear')}
                </span>
              </p>
              {billing === 'yearly' && (
                <p className="text-xs text-success font-medium">{t('pricing.yearlySavings')}</p>
              )}
            </div>
          </div>
          <ul className="space-y-2.5 mb-5">
            <PlanFeature icon={<BookOpen className="w-4 h-4" />} text={t('pricing.proFeature1')} highlighted />
            <PlanFeature icon={<Brain className="w-4 h-4" />} text={t('pricing.proFeature2')} highlighted />
            <PlanFeature icon={<PenTool className="w-4 h-4" />} text={t('pricing.proFeature3')} highlighted />
            <PlanFeature icon={<CalendarClock className="w-4 h-4" />} text={t('pricing.proFeature4')} highlighted />
            <PlanFeature icon={<Sparkles className="w-4 h-4" />} text={t('pricing.proFeature5')} highlighted />
          </ul>
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full bg-student-blue text-white py-3 rounded-xl font-semibold hover:bg-student-blue/90 transition disabled:opacity-50"
          >
            {loading ? t('common.loading') : t('pricing.upgradeToPro')}
          </button>
        </div>
      </div>

      {/* Usage Info */}
      {subscription && !subscription.has_pro && (
        <div className="mt-4 bg-gold-accent/10 border border-gold-accent/30 rounded-xl p-4 text-center">
          <p className="text-sm text-text-primary">
            {t('pricing.freeUsage', {
              used: subscription.ai_generations_used,
              limit: subscription.ai_generations_limit,
            })}
          </p>
        </div>
      )}

      <p className="text-center text-xs text-dark-gray mt-6">
        {t('pricing.guarantee')}
      </p>
    </div>
  );
}

function PlanFeature({ icon, text, highlighted }: { icon: React.ReactNode; text: string; highlighted?: boolean }) {
  return (
    <li className="flex items-center gap-2.5 text-sm">
      <div className={`${highlighted ? 'text-student-blue' : 'text-dark-gray'}`}>
        {icon}
      </div>
      <span className={highlighted ? 'text-text-primary font-medium' : 'text-dark-gray'}>{text}</span>
    </li>
  );
}
