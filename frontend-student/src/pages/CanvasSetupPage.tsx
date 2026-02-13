import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Link2, CheckCircle, ArrowRight, Loader2, ExternalLink, School } from 'lucide-react';
import api from '../lib/api';
import { useAuthStore } from '../stores/authStore';

// School detection database — same as Educator Edition
const SCHOOL_MAP: Record<string, string> = {
  'vuu.instructure.com': 'Virginia Union University (VUU)',
  'howard.instructure.com': 'Howard University',
  'spelman.instructure.com': 'Spelman College',
  'morehouse.instructure.com': 'Morehouse College',
  'yale.instructure.com': 'Yale University',
  'harvard.instructure.com': 'Harvard University',
  'mit.instructure.com': 'MIT',
  'stanford.instructure.com': 'Stanford University',
  'columbia.instructure.com': 'Columbia University',
  'ncat.instructure.com': 'North Carolina A&T State University',
  'famu.instructure.com': 'Florida A&M University',
  'hampton.instructure.com': 'Hampton University',
  'tuskegee.instructure.com': 'Tuskegee University',
  'bcuedu.instructure.com': 'Bethune-Cookman University',
  'xula.instructure.com': 'Xavier University of Louisiana',
};

// Map email domains to Canvas URLs for auto-detection
const EMAIL_TO_CANVAS: Record<string, string> = {
  'mymail.vuu.edu': 'https://vuu.instructure.com',
  'vuu.edu': 'https://vuu.instructure.com',
  'howard.edu': 'https://howard.instructure.com',
  'spelman.edu': 'https://spelman.instructure.com',
  'morehouse.edu': 'https://morehouse.instructure.com',
  'yale.edu': 'https://yale.instructure.com',
  'harvard.edu': 'https://harvard.instructure.com',
  'mit.edu': 'https://mit.instructure.com',
  'stanford.edu': 'https://stanford.instructure.com',
  'columbia.edu': 'https://columbia.instructure.com',
  'ncat.edu': 'https://ncat.instructure.com',
  'famu.edu': 'https://famu.instructure.com',
  'hamptonu.edu': 'https://hampton.instructure.com',
  'tuskegee.edu': 'https://tuskegee.instructure.com',
  'cookman.edu': 'https://bcuedu.instructure.com',
  'xula.edu': 'https://xula.instructure.com',
};

function detectSchool(url: string) {
  const clean = url.replace(/^https?:\/\//, '').replace(/\/.*$/, '').trim();
  const isCanvas = clean.includes('instructure.com');
  const name = SCHOOL_MAP[clean] || null;
  const shortName = name ? name.split('(')[0].trim() : null;
  return { isCanvas, name, shortName, cleanDomain: clean };
}

export default function CanvasSetupPage() {
  const { user } = useAuthStore();
  const [canvasUrl, setCanvasUrl] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [status, setStatus] = useState<'idle' | 'connecting' | 'syncing' | 'done' | 'error'>('idle');
  const [error, setError] = useState('');
  const [coursesFound, setCoursesFound] = useState(0);
  const navigate = useNavigate();

  // Auto-detect Canvas URL from user's email domain
  useEffect(() => {
    if (user?.email && !canvasUrl) {
      const domain = user.email.split('@')[1]?.toLowerCase();
      if (domain && EMAIL_TO_CANVAS[domain]) {
        setCanvasUrl(EMAIL_TO_CANVAS[domain]);
      }
    }
  }, [user]);

  const school = useMemo(() => detectSchool(canvasUrl), [canvasUrl]);

  const openCanvasSettings = () => {
    if (school.isCanvas && school.cleanDomain) {
      window.open(`https://${school.cleanDomain}/profile/settings`, '_blank');
    }
  };

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('connecting');
    setError('');

    try {
      const connectRes = await api.post('/api/v1/student/canvas/connect', {
        canvas_url: canvasUrl,
        access_token: accessToken,
      });

      setCoursesFound(connectRes.data.courses_found);

      setStatus('syncing');
      await api.post('/api/v1/student/courses/sync');

      await Promise.all([
        api.post('/api/v1/student/announcements/sync'),
        api.post('/api/v1/student/assignments/sync'),
      ]);

      setStatus('done');
      setTimeout(() => navigate('/dashboard'), 1500);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Connection failed. Check your URL and token.');
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-light-gray flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        <div className="text-center mb-8">
          <Link2 className="w-12 h-12 text-student-blue mx-auto mb-3" />
          <h1 className="text-2xl font-bold text-navy-primary">Connect Canvas</h1>
          <p className="text-dark-gray mt-1">Link your Canvas account to get started</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          {status === 'done' ? (
            <div className="text-center py-8">
              <CheckCircle className="w-16 h-16 text-success mx-auto mb-4" />
              <h2 className="text-xl font-bold text-text-primary mb-2">All set!</h2>
              <p className="text-dark-gray mb-4">
                Found {coursesFound} course{coursesFound !== 1 ? 's' : ''}. Your dashboard is ready!
              </p>
              <button
                onClick={() => navigate('/dashboard')}
                className="bg-student-blue text-white px-6 py-3 rounded-lg font-semibold hover:bg-student-blue/90 transition flex items-center gap-2 mx-auto"
              >
                Go to Dashboard <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <>
              {error && (
                <div className="bg-error/10 border border-error/20 text-error rounded-lg px-4 py-3 mb-4 text-sm">
                  {error}
                </div>
              )}

              <form onSubmit={handleConnect} className="space-y-4">
                {/* Canvas URL with school detection */}
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1">
                    Canvas URL
                  </label>
                  <input
                    type="text"
                    value={canvasUrl}
                    onChange={(e) => setCanvasUrl(e.target.value)}
                    required
                    placeholder="https://your-school.instructure.com"
                    className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base"
                  />

                  {/* School Detection Badge */}
                  {school.isCanvas && school.name && (
                    <div className="flex items-center gap-2 mt-2 text-success text-sm font-medium">
                      <School className="w-4 h-4" />
                      {school.name} detected!
                    </div>
                  )}
                  {school.isCanvas && !school.name && school.cleanDomain.length > 5 && (
                    <p className="text-xs text-dark-gray mt-1">Canvas instance detected</p>
                  )}
                  {!school.isCanvas && canvasUrl.length === 0 && (
                    <p className="text-xs text-dark-gray mt-1">Your school's Canvas web address</p>
                  )}
                </div>

                {/* Instructions — personalized with school name */}
                <div className="bg-sky-blue/20 rounded-lg p-4">
                  <h3 className="font-semibold text-navy-primary text-sm mb-2">
                    How to get your Canvas token:
                  </h3>
                  <ol className="text-sm text-dark-gray space-y-1 list-decimal list-inside">
                    <li>Click the button below to open {school.shortName || 'your'} Canvas Settings</li>
                    <li>Scroll to <strong>Approved Integrations</strong></li>
                    <li>Click <strong>+ New Access Token</strong></li>
                    <li>Set purpose: <strong>"ReadySetClass"</strong> and click <strong>Generate Token</strong></li>
                    <li>Copy the token and paste it below</li>
                  </ol>

                  <button
                    type="button"
                    onClick={openCanvasSettings}
                    disabled={!school.isCanvas}
                    className="mt-3 w-full bg-student-blue text-white py-2.5 rounded-lg font-semibold text-sm
                      hover:bg-student-blue/90 transition disabled:opacity-40 disabled:cursor-not-allowed
                      flex items-center justify-center gap-2"
                  >
                    <ExternalLink className="w-4 h-4" />
                    Open {school.shortName || 'Canvas'} Settings
                  </button>
                </div>

                {/* Access Token */}
                <div>
                  <label className="block text-sm font-medium text-text-primary mb-1">
                    Access Token
                  </label>
                  <input
                    type="password"
                    value={accessToken}
                    onChange={(e) => setAccessToken(e.target.value)}
                    required
                    placeholder="Paste your Canvas API token"
                    className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base font-mono text-sm"
                  />
                </div>

                <button
                  type="submit"
                  disabled={status === 'connecting' || status === 'syncing'}
                  className="w-full bg-navy-primary text-white py-3 rounded-lg font-semibold text-base hover:bg-navy-hover transition disabled:opacity-50 disabled:cursor-not-allowed min-h-[48px] flex items-center justify-center gap-2"
                >
                  {status === 'connecting' || status === 'syncing' ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      {status === 'connecting' ? 'Connecting...' : 'Syncing courses...'}
                    </>
                  ) : (
                    'Connect Canvas'
                  )}
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
