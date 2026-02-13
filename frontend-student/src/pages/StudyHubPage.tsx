import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Brain, BookOpen, PenTool, CalendarClock, Sparkles, Crown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useSubscriptionStore } from '../stores/subscriptionStore';

export default function StudyHubPage() {
  const { t } = useTranslation();
  const { subscription, fetchStatus } = useSubscriptionStore();

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const tools = [
    {
      to: '/study/flashcards',
      icon: <BookOpen className="w-7 h-7" />,
      color: 'bg-violet-500',
      title: t('study.flashcards'),
      desc: t('study.flashcardsDesc'),
    },
    {
      to: '/study/quiz',
      icon: <Brain className="w-7 h-7" />,
      color: 'bg-student-blue',
      title: t('study.quiz'),
      desc: t('study.quizDesc'),
    },
    {
      to: '/study/writing',
      icon: <PenTool className="w-7 h-7" />,
      color: 'bg-emerald-500',
      title: t('study.writing'),
      desc: t('study.writingDesc'),
    },
    {
      to: '/study/schedule',
      icon: <CalendarClock className="w-7 h-7" />,
      color: 'bg-gold-accent',
      title: t('study.schedule'),
      desc: t('study.scheduleDesc'),
    },
  ];

  const atLimit = subscription && !subscription.has_pro &&
    subscription.ai_generations_used >= subscription.ai_generations_limit;

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="w-5 h-5 text-student-blue" />
        <h1 className="text-2xl font-bold text-navy-primary">{t('study.title')}</h1>
      </div>
      <p className="text-dark-gray text-sm mb-6">{t('study.subtitle')}</p>

      {/* Usage / Upgrade Banner */}
      {subscription && !subscription.has_pro && (
        <Link
          to="/pricing"
          className={`block rounded-xl p-4 mb-4 transition ${
            atLimit
              ? 'bg-error/10 border border-error/30'
              : 'bg-gold-accent/10 border border-gold-accent/30'
          }`}
        >
          <div className="flex items-center gap-3">
            <Crown className={`w-5 h-5 ${atLimit ? 'text-error' : 'text-gold-accent'}`} />
            <div className="flex-1">
              <p className="text-sm font-semibold text-text-primary">
                {atLimit ? t('study.limitReached') : t('study.freeUsage', {
                  used: subscription.ai_generations_used,
                  limit: subscription.ai_generations_limit,
                })}
              </p>
              <p className="text-xs text-dark-gray">{t('study.upgradeHint')}</p>
            </div>
          </div>
        </Link>
      )}

      {subscription?.has_pro && (
        <div className="bg-student-blue/10 border border-student-blue/20 rounded-xl p-3 mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-student-blue" />
          <p className="text-sm font-medium text-student-blue">{t('study.proActive')}</p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3">
        {tools.map((tool) => (
          <Link
            key={tool.to}
            to={tool.to}
            className="bg-white rounded-xl shadow-sm p-5 hover:shadow-md transition flex items-center gap-4"
          >
            <div className={`${tool.color} text-white w-14 h-14 rounded-xl flex items-center justify-center shrink-0`}>
              {tool.icon}
            </div>
            <div>
              <h3 className="font-semibold text-text-primary">{tool.title}</h3>
              <p className="text-sm text-dark-gray mt-0.5">{tool.desc}</p>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
