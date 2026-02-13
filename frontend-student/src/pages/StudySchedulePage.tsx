import { useEffect } from 'react';
import { CalendarClock, RefreshCw, Loader2, Clock, BookOpen, AlertTriangle } from 'lucide-react';
import { useStudyStore } from '../stores/studyStore';

export default function StudySchedulePage() {
  const { schedule, scheduleLoading, fetchSchedule, refreshSchedule } = useStudyStore();

  useEffect(() => {
    fetchSchedule();
  }, [fetchSchedule]);

  const priorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'border-l-error bg-error/5';
      case 'medium': return 'border-l-gold-accent bg-gold-accent/5';
      default: return 'border-l-success bg-success/5';
    }
  };

  const priorityBadge = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'bg-error/10 text-error';
      case 'medium': return 'bg-gold-accent/10 text-gold-accent';
      default: return 'bg-success/10 text-success';
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2">
          <CalendarClock className="w-5 h-5 text-gold-accent" /> Study Schedule
        </h1>
        <button
          onClick={refreshSchedule}
          disabled={scheduleLoading}
          className="text-student-blue hover:bg-student-blue/10 p-2 rounded-lg transition disabled:opacity-50"
          title="Regenerate schedule"
        >
          <RefreshCw className={`w-5 h-5 ${scheduleLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-dark-gray text-sm mb-6">AI-generated study plan based on your deadlines</p>

      {scheduleLoading ? (
        <div className="flex flex-col items-center py-16 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-student-blue" />
          <p className="text-dark-gray text-sm">Building your personalized study plan...</p>
        </div>
      ) : !schedule ? (
        <div className="text-center py-12">
          <CalendarClock className="w-12 h-12 text-student-blue/30 mx-auto mb-3" />
          <p className="text-dark-gray font-medium">No schedule generated yet</p>
          <p className="text-sm text-dark-gray mt-1">Connect Canvas and sync your courses first</p>
          <button
            onClick={refreshSchedule}
            className="mt-4 bg-student-blue text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:bg-student-blue/90 transition"
          >
            Generate Study Plan
          </button>
        </div>
      ) : (
        <>
          {/* Summary */}
          <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
            <p className="text-sm text-text-primary leading-relaxed">{schedule.summary}</p>
            {schedule.generated_for && (
              <p className="text-xs text-dark-gray mt-2">
                Generated for: {schedule.generated_for}
              </p>
            )}
          </div>

          {/* Schedule blocks */}
          <div className="space-y-2 mb-6">
            {schedule.schedule.map((block, i) => (
              <div
                key={i}
                className={`bg-white rounded-xl shadow-sm p-4 border-l-4 ${priorityColor(block.priority)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Clock className="w-3.5 h-3.5 text-dark-gray" />
                      <span className="text-xs font-medium text-dark-gray">{block.time}</span>
                      <span className="text-xs text-dark-gray">({block.duration_minutes} min)</span>
                    </div>
                    <p className="font-semibold text-text-primary text-sm">{block.task}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <BookOpen className="w-3 h-3 text-dark-gray" />
                      <span className="text-xs text-dark-gray">{block.course}</span>
                    </div>
                  </div>
                  <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${priorityBadge(block.priority)}`}>
                    {block.priority}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Tips */}
          {schedule.tips && schedule.tips.length > 0 && (
            <div className="bg-gold-accent/10 border border-gold-accent/20 rounded-xl p-4">
              <h3 className="font-semibold text-navy-primary text-sm flex items-center gap-2 mb-2">
                <AlertTriangle className="w-4 h-4 text-gold-accent" /> Study Tips
              </h3>
              <ul className="space-y-1.5">
                {schedule.tips.map((tip, i) => (
                  <li key={i} className="text-sm text-dark-gray flex items-start gap-2">
                    <span className="text-gold-accent font-bold mt-0.5">•</span>
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}
