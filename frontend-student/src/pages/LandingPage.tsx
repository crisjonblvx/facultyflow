import { useNavigate } from 'react-router-dom';
import {
  Bell, CheckCircle, BarChart3, Calendar, Brain, Sparkles,
  ChevronDown, ChevronUp, Smartphone, PenTool,
  ArrowRight, X, Check
} from 'lucide-react';
import { useState } from 'react';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white">
      {/* Sticky Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-medium-gray/50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <img src="/logo.png" alt="ReadySetClass" className="h-8" />
          <div className="flex items-center gap-3">
            <button
              onClick={() => navigate('/login')}
              className="text-sm font-medium text-navy-primary hover:text-student-blue transition"
            >
              Log in
            </button>
            <button
              onClick={() => navigate('/register')}
              className="bg-student-blue text-white text-sm font-semibold px-4 py-2 rounded-lg hover:bg-student-blue/90 transition"
            >
              Start Free
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="px-4 pt-12 pb-16 md:pt-20 md:pb-24 bg-gradient-to-b from-white to-light-gray">
        <div className="max-w-3xl mx-auto text-center">
          <div className="inline-flex items-center gap-1.5 bg-student-blue/10 text-student-blue text-xs font-semibold px-3 py-1.5 rounded-full mb-6">
            <Sparkles className="w-3.5 h-3.5" />
            Student Edition
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-navy-primary leading-tight mb-4">
            Canvas, but it actually
            <span className="text-student-blue"> works for you</span>
          </h1>
          <p className="text-lg md:text-xl text-dark-gray max-w-xl mx-auto mb-8 leading-relaxed">
            Never miss an announcement. Submit with confidence. Always know your grade. AI study tools that actually help.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              onClick={() => navigate('/register')}
              className="w-full sm:w-auto bg-student-blue text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-student-blue/90 transition text-base flex items-center justify-center gap-2"
            >
              Start Free — No Credit Card
              <ArrowRight className="w-4 h-4" />
            </button>
            <a
              href="#features"
              className="w-full sm:w-auto text-navy-primary font-medium px-6 py-3.5 rounded-xl border border-medium-gray hover:bg-light-gray transition text-base text-center"
            >
              See How It Works
            </a>
          </div>
          <p className="text-xs text-dark-gray mt-4">
            3 free AI uses per month. Upgrade anytime for $4.99/mo.
          </p>
        </div>
      </section>

      {/* Pain Points */}
      <section className="px-4 py-14 md:py-20 bg-navy-primary text-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-center mb-10">
            Sound familiar?
          </h2>
          <div className="space-y-4 max-w-xl mx-auto">
            {[
              '"I missed the announcement that class was cancelled"',
              '"My professor can\'t open my Google Drive file"',
              '"I have no idea what grade I need on the final"',
              '"Canvas notifications never actually work"',
              '"I submitted the wrong file and lost points"',
            ].map((pain, i) => (
              <div key={i} className="flex items-start gap-3 bg-white/10 rounded-xl px-4 py-3">
                <X className="w-5 h-5 text-error shrink-0 mt-0.5" />
                <p className="text-sm md:text-base text-white/90">{pain}</p>
              </div>
            ))}
          </div>
          <p className="text-center mt-10 text-white/80 text-base">
            You're not alone. Canvas is frustrating for everyone.
          </p>
          <p className="text-center mt-1 text-gold-accent font-semibold text-lg">
            ReadySetClass fixes it.
          </p>
        </div>
      </section>

      {/* How It Works */}
      <section className="px-4 py-14 md:py-20 bg-light-gray">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-navy-primary mb-3">
            It's stupid simple
          </h2>
          <p className="text-dark-gray mb-10">Set up in 2 minutes. Seriously.</p>
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '1', icon: Smartphone, title: 'Connect Canvas', desc: 'Paste your Canvas token. Takes 60 seconds.' },
              { step: '2', icon: Bell, title: 'Get Real Alerts', desc: 'Urgency detection catches what matters — cancelled classes, moved deadlines.' },
              { step: '3', icon: Sparkles, title: 'Study Smarter', desc: 'AI flashcards, quizzes, writing help, and study schedules from your actual courses.' },
            ].map(({ step, icon: Icon, title, desc }) => (
              <div key={step} className="bg-white rounded-2xl p-6 shadow-sm">
                <div className="w-10 h-10 bg-student-blue/10 text-student-blue font-bold rounded-full flex items-center justify-center mx-auto mb-4 text-lg">
                  {step}
                </div>
                <Icon className="w-8 h-8 text-student-blue mx-auto mb-3" />
                <h3 className="font-bold text-navy-primary mb-2">{title}</h3>
                <p className="text-sm text-dark-gray">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="px-4 py-14 md:py-20 bg-white scroll-mt-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-navy-primary text-center mb-3">
            What you get
          </h2>
          <p className="text-dark-gray text-center mb-12">
            Everything a student actually needs from Canvas — and nothing you don't.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <FeatureCard
              icon={Bell}
              color="text-error"
              bg="bg-error/10"
              title="Announcement Alerts"
              desc="Push notifications for urgent stuff — class cancellations, room changes, deadline extensions. Daily digest for everything else."
              benefit="Never miss important info again."
            />
            <FeatureCard
              icon={CheckCircle}
              color="text-success"
              bg="bg-success/10"
              title="Submission Checker"
              desc={'Checks your files BEFORE you submit. "Your professor can\'t access this Google Drive link" — fix it before it costs you points.'}
              benefit="No more lost points for technical errors."
            />
            <FeatureCard
              icon={BarChart3}
              color="text-student-blue"
              bg="bg-student-blue/10"
              title="Grade Calculator"
              desc='"What do I need on the final to get an A?" See it instantly. What-if scenarios for any assignment.'
              benefit="No spreadsheet needed."
            />
            <FeatureCard
              icon={Calendar}
              color="text-warning"
              bg="bg-warning/10"
              title="One Deadline View"
              desc="All your courses. All your due dates. One place. Filter by overdue, upcoming, or submitted."
              benefit="Actually know what's due when."
            />
            <FeatureCard
              icon={Brain}
              color="text-purple-600"
              bg="bg-purple-100"
              title="AI Flashcards & Quizzes"
              desc="Paste your notes → get study cards. Pick a topic → get a practice quiz. AI-powered, instant, and personalized."
              benefit="Study in half the time."
            />
            <FeatureCard
              icon={PenTool}
              color="text-gold-accent"
              bg="bg-gold-accent/10"
              title="AI Writing Help"
              desc="Brainstorm ideas, build outlines, get feedback on drafts, strengthen arguments. Your writing, improved."
              benefit="Not writing for you — writing WITH you."
            />
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="px-4 py-14 md:py-20 bg-light-gray scroll-mt-16">
        <PricingSection onGetStarted={() => navigate('/register')} />
      </section>

      {/* FAQ */}
      <section className="px-4 py-14 md:py-20 bg-white">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl md:text-3xl font-bold text-navy-primary text-center mb-10">
            Questions?
          </h2>
          <div className="space-y-3">
            <FAQItem
              q="Is this allowed by my school?"
              a="Yes. We use Canvas's official API — the same one the Canvas mobile app uses. Your school doesn't need to approve anything."
            />
            <FAQItem
              q="Can you see my grades and assignments?"
              a="Only you can see your data. Your Canvas token is encrypted and never shared. We don't sell data, ever."
            />
            <FAQItem
              q="Does it work on iPhone and Android?"
              a="Yes! It's a web app that works on any device — iPhone, Android, laptop, tablet. Add it to your home screen for the best experience."
            />
            <FAQItem
              q="What if I drop or add a class?"
              a="Hit sync and it auto-updates. Your courses, grades, and deadlines refresh from Canvas in seconds."
            />
            <FAQItem
              q="Do professors know I'm using this?"
              a="Nope. ReadySetClass is read-only — it pulls data from Canvas but never posts anything. It's just for you."
            />
            <FAQItem
              q="Does the AI write my papers for me?"
              a="No — and that's intentional. The AI helps you brainstorm, outline, and strengthen YOUR writing. It won't generate essays or do your homework."
            />
            <FAQItem
              q="Can I cancel anytime?"
              a="Yes. Cancel in settings with one tap. No questions, no fees, no guilt trip emails."
            />
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="px-4 py-16 md:py-24 bg-navy-primary text-white text-center">
        <div className="max-w-xl mx-auto">
          <img src="/logo.png" alt="ReadySetClass" className="h-14 mx-auto mb-4 brightness-0 invert" />
          <h2 className="text-2xl md:text-3xl font-bold mb-3">
            Stop fighting Canvas.
          </h2>
          <p className="text-white/80 mb-8 text-base">
            Free to start. 3 AI uses per month included. No credit card required.
          </p>
          <button
            onClick={() => navigate('/register')}
            className="bg-gold-accent text-navy-primary font-bold px-8 py-4 rounded-xl hover:bg-gold-accent/90 transition text-base flex items-center justify-center gap-2 mx-auto"
          >
            Start Free — Takes 2 Minutes
            <ArrowRight className="w-4 h-4" />
          </button>
          <p className="text-white/50 text-xs mt-6">
            ReadySetClass Student Edition v1.0
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-navy-hover text-white/60 text-xs px-4 py-6">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <img src="/logo.png" alt="ReadySetClass" className="h-5 brightness-0 invert opacity-60" />
          <p>&copy; {new Date().getFullYear()} ReadySetClass. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}

/* ── Sub-components ── */

function FeatureCard({
  icon: Icon, color, bg, title, desc, benefit,
}: {
  icon: React.ElementType; color: string; bg: string; title: string; desc: string; benefit: string;
}) {
  return (
    <div className="bg-light-gray rounded-2xl p-6 hover:shadow-md transition">
      <div className={`w-10 h-10 ${bg} rounded-xl flex items-center justify-center mb-4`}>
        <Icon className={`w-5 h-5 ${color}`} />
      </div>
      <h3 className="font-bold text-navy-primary mb-2 text-lg">{title}</h3>
      <p className="text-sm text-dark-gray mb-3 leading-relaxed">{desc}</p>
      <p className="text-sm font-semibold text-navy-primary">{benefit}</p>
    </div>
  );
}

function PricingSection({ onGetStarted }: { onGetStarted: () => void }) {
  const [billing, setBilling] = useState<'monthly' | 'yearly'>('monthly');

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-2xl md:text-3xl font-bold text-navy-primary text-center mb-3">
        Simple pricing
      </h2>
      <p className="text-dark-gray text-center mb-8">
        Start free. Upgrade when you're ready.
      </p>

      {/* Toggle */}
      <div className="flex items-center justify-center gap-2 mb-8">
        <button
          onClick={() => setBilling('monthly')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            billing === 'monthly'
              ? 'bg-student-blue text-white'
              : 'bg-white text-dark-gray border border-medium-gray'
          }`}
        >
          Monthly
        </button>
        <button
          onClick={() => setBilling('yearly')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
            billing === 'yearly'
              ? 'bg-student-blue text-white'
              : 'bg-white text-dark-gray border border-medium-gray'
          }`}
        >
          Yearly
          <span className="ml-1 text-xs opacity-80">(save 17%)</span>
        </button>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Free */}
        <div className="bg-white rounded-2xl p-6 border-2 border-medium-gray">
          <h3 className="text-xl font-bold text-text-primary mb-1">Free</h3>
          <p className="text-3xl font-extrabold text-text-primary mb-1">
            $0<span className="text-sm font-normal text-dark-gray">/mo</span>
          </p>
          <p className="text-xs text-dark-gray mb-6">Free forever</p>
          <ul className="space-y-3 mb-6">
            <PriceFeature text="Canvas sync — courses, grades, deadlines" />
            <PriceFeature text="Announcement alerts with urgency detection" />
            <PriceFeature text="Submission checker" />
            <PriceFeature text="Grade calculator & deadline view" />
            <PriceFeature text="3 free AI study tool uses per month" />
          </ul>
          <button
            onClick={onGetStarted}
            className="w-full py-3 rounded-xl font-semibold border-2 border-navy-primary text-navy-primary hover:bg-navy-primary hover:text-white transition"
          >
            Get Started Free
          </button>
        </div>

        {/* Pro */}
        <div className="bg-white rounded-2xl p-6 border-2 border-student-blue relative">
          <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gold-accent text-white text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap">
            MOST POPULAR
          </div>
          <h3 className="text-xl font-bold text-student-blue flex items-center gap-1.5 mb-1">
            <Sparkles className="w-5 h-5" />
            Student Pro
          </h3>
          <p className="text-3xl font-extrabold text-text-primary mb-1">
            {billing === 'monthly' ? '$4.99' : '$49.99'}
            <span className="text-sm font-normal text-dark-gray">
              {billing === 'monthly' ? '/mo' : '/yr'}
            </span>
          </p>
          {billing === 'yearly' && (
            <p className="text-xs text-success font-medium mb-4">Save $9.89 vs. monthly</p>
          )}
          {billing === 'monthly' && <p className="text-xs text-dark-gray mb-4">Less than a coffee per month</p>}
          <ul className="space-y-3 mb-6">
            <PriceFeature text="Everything in Free, plus..." highlighted />
            <PriceFeature text="Unlimited AI flashcard generation" highlighted />
            <PriceFeature text="Unlimited AI practice quizzes" highlighted />
            <PriceFeature text="Unlimited AI writing assistance" highlighted />
            <PriceFeature text="Unlimited AI study schedules" highlighted />
          </ul>
          <button
            onClick={onGetStarted}
            className="w-full bg-student-blue text-white py-3 rounded-xl font-semibold hover:bg-student-blue/90 transition"
          >
            Start Free, Upgrade Later
          </button>
        </div>
      </div>

      <p className="text-center text-xs text-dark-gray mt-6">
        Cancel anytime. No questions asked. That's less than a Starbucks per month.
      </p>
    </div>
  );
}

function PriceFeature({ text, highlighted }: { text: string; highlighted?: boolean }) {
  return (
    <li className="flex items-start gap-2.5 text-sm">
      <Check className={`w-4 h-4 shrink-0 mt-0.5 ${highlighted ? 'text-student-blue' : 'text-success'}`} />
      <span className={highlighted ? 'text-text-primary font-medium' : 'text-dark-gray'}>{text}</span>
    </li>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-medium-gray rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-light-gray transition"
      >
        <span className="font-semibold text-navy-primary text-sm pr-4">{q}</span>
        {open ? (
          <ChevronUp className="w-4 h-4 text-dark-gray shrink-0" />
        ) : (
          <ChevronDown className="w-4 h-4 text-dark-gray shrink-0" />
        )}
      </button>
      {open && (
        <div className="px-5 pb-4 text-sm text-dark-gray leading-relaxed">
          {a}
        </div>
      )}
    </div>
  );
}
