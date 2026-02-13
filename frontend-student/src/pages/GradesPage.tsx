import { useEffect, useState } from 'react';
import { BarChart3, ChevronDown, ChevronUp, RefreshCw, Loader2, TrendingUp, Calculator } from 'lucide-react';
import { useGradeStore } from '../stores/gradeStore';
import api from '../lib/api';
import type { CourseGrade } from '../types';

function GradeRing({ percentage, letter, size = 64 }: { percentage: number | null; letter: string | null; size?: number }) {
  const pct = percentage ?? 0;
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  const color = pct >= 90 ? '#10b981' : pct >= 80 ? '#4A90E2' : pct >= 70 ? '#D4AF37' : pct >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth="4" />
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke={color} strokeWidth="4"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          className="transition-all duration-500" />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-sm font-bold text-text-primary">{letter || '--'}</span>
      </div>
    </div>
  );
}

function CourseGradeCard({ course }: { course: CourseGrade }) {
  const [expanded, setExpanded] = useState(false);
  const [showWhatIf, setShowWhatIf] = useState(false);
  const [targetGrade, setTargetGrade] = useState('90');
  const [whatIfResult, setWhatIfResult] = useState<any>(null);
  const [calculating, setCalculating] = useState(false);

  const handleWhatIf = async () => {
    setCalculating(true);
    try {
      const res = await api.post('/api/v1/student/grades/what-if', {
        course_id: course.course_id,
        scenario_type: 'target_grade',
        target_grade: parseFloat(targetGrade),
      });
      setWhatIfResult(res.data.result);
    } catch {
      // silent
    } finally {
      setCalculating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-4 flex items-center gap-4 text-left hover:bg-light-gray/50 transition"
      >
        <GradeRing percentage={course.current_percentage} letter={course.current_letter} />
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-text-primary text-sm leading-tight">{course.course_name}</h3>
          <p className="text-xs text-dark-gray mt-0.5">{course.course_code}</p>
          {course.current_percentage !== null && (
            <p className="text-xs font-medium text-dark-gray mt-1">
              {course.current_percentage.toFixed(1)}% &middot; {course.points_earned}/{course.points_possible} pts
            </p>
          )}
        </div>
        {expanded ? <ChevronUp className="w-5 h-5 text-dark-gray" /> : <ChevronDown className="w-5 h-5 text-dark-gray" />}
      </button>

      {expanded && (
        <div className="border-t border-medium-gray px-4 pb-4">
          {/* Category Breakdown */}
          {course.category_scores.length > 0 && (
            <div className="mt-3">
              <h4 className="text-xs font-semibold text-dark-gray uppercase mb-2">Category Breakdown</h4>
              <div className="space-y-2">
                {course.category_scores.map((cat) => (
                  <div key={cat.name}>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-text-primary font-medium">{cat.name}</span>
                      <span className="text-dark-gray">
                        {cat.percentage.toFixed(1)}%
                        {cat.weight ? ` (${cat.weight}%)` : ''}
                      </span>
                    </div>
                    <div className="w-full bg-medium-gray rounded-full h-1.5 mt-1">
                      <div
                        className="h-1.5 rounded-full transition-all duration-500"
                        style={{
                          width: `${Math.min(cat.percentage, 100)}%`,
                          backgroundColor: cat.percentage >= 90 ? '#10b981' : cat.percentage >= 80 ? '#4A90E2' : cat.percentage >= 70 ? '#D4AF37' : '#ef4444',
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-dark-gray mt-0.5">
                      {cat.graded_count}/{cat.total_count} graded &middot; {cat.points_earned}/{cat.points_possible} pts
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* What-If Calculator */}
          <div className="mt-4 pt-3 border-t border-medium-gray">
            <button
              onClick={() => setShowWhatIf(!showWhatIf)}
              className="flex items-center gap-2 text-sm font-medium text-student-blue"
            >
              <Calculator className="w-4 h-4" />
              What-If Calculator
            </button>

            {showWhatIf && (
              <div className="mt-3 bg-sky-blue/10 rounded-lg p-3">
                <p className="text-xs text-dark-gray mb-2">What grade do you want to achieve?</p>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={targetGrade}
                    onChange={(e) => setTargetGrade(e.target.value)}
                    min="0"
                    max="100"
                    className="w-20 px-3 py-2 border border-medium-gray rounded-lg text-sm text-center"
                  />
                  <span className="self-center text-sm text-dark-gray">%</span>
                  <button
                    onClick={handleWhatIf}
                    disabled={calculating}
                    className="flex-1 bg-student-blue text-white text-sm py-2 px-4 rounded-lg font-medium disabled:opacity-50 flex items-center justify-center gap-1"
                  >
                    {calculating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Calculate'}
                  </button>
                </div>

                {whatIfResult && (
                  <div className={`mt-3 p-3 rounded-lg text-sm ${
                    whatIfResult.achievable ? 'bg-success/10 text-success' : 'bg-error/10 text-error'
                  }`}>
                    <p className="font-medium">{whatIfResult.message}</p>
                    {whatIfResult.achievable && whatIfResult.needed_percentage !== undefined && (
                      <p className="text-xs mt-1 opacity-80">
                        Need {whatIfResult.needed_percentage.toFixed(1)}% average on remaining work
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default function GradesPage() {
  const { grades, loading, syncing, fetchGrades, syncGrades } = useGradeStore();

  useEffect(() => {
    fetchGrades();
  }, [fetchGrades]);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Grades
        </h1>
        <button
          onClick={syncGrades}
          disabled={syncing}
          className="flex items-center gap-1.5 text-sm text-student-blue font-medium disabled:opacity-50"
        >
          {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Sync
        </button>
      </div>

      {/* GPA Estimate */}
      {grades?.gpa_estimate !== null && grades?.gpa_estimate !== undefined && (
        <div className="bg-navy-primary text-white rounded-xl p-4 mb-4 flex items-center gap-4">
          <TrendingUp className="w-8 h-8 text-gold-accent" />
          <div>
            <p className="text-xs text-white/70 font-medium">Estimated GPA</p>
            <p className="text-2xl font-bold">{grades.gpa_estimate.toFixed(2)}</p>
          </div>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-student-blue" />
        </div>
      ) : !grades || grades.courses.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-8 text-center">
          <BarChart3 className="w-12 h-12 text-medium-gray mx-auto mb-3" />
          <h3 className="font-semibold text-dark-gray mb-1">No grades yet</h3>
          <p className="text-sm text-dark-gray">
            Sync your assignments first to see grade breakdowns.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {grades.courses.map((course) => (
            <CourseGradeCard key={course.course_id} course={course} />
          ))}
        </div>
      )}
    </div>
  );
}
