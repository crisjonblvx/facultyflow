import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, CheckCircle, AlertTriangle, ExternalLink, RefreshCw, Loader2, Upload } from 'lucide-react';
import { useAssignmentStore } from '../stores/assignmentStore';
import { format } from 'date-fns';
import type { Assignment, AssignmentFilter } from '../types';

const FILTERS: { key: AssignmentFilter; label: string }[] = [
  { key: 'upcoming', label: 'Upcoming' },
  { key: 'overdue', label: 'Overdue' },
  { key: 'unsubmitted', label: 'To Do' },
  { key: 'submitted', label: 'Submitted' },
  { key: 'graded', label: 'Graded' },
  { key: 'all', label: 'All' },
];

function AssignmentCard({ assignment }: { assignment: Assignment }) {
  const urgencyColor = assignment.is_overdue
    ? 'border-l-error'
    : assignment.is_upcoming
    ? 'border-l-gold-accent'
    : 'border-l-success';

  const statusBadge = assignment.submitted
    ? assignment.graded
      ? { text: `${assignment.grade || assignment.score}/${assignment.points_possible}`, color: 'bg-student-blue/10 text-student-blue' }
      : { text: 'Submitted', color: 'bg-success/10 text-success' }
    : assignment.is_overdue
    ? { text: 'Overdue', color: 'bg-error/10 text-error' }
    : null;

  return (
    <div className={`bg-white rounded-lg shadow-sm border-l-4 ${urgencyColor} p-4`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-student-blue mb-1">{assignment.course_name}</p>
          <h3 className="font-semibold text-text-primary text-sm leading-tight">{assignment.name}</h3>

          <div className="flex items-center gap-3 mt-2 text-xs text-dark-gray">
            {assignment.due_at && (
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {format(new Date(assignment.due_at), 'MMM d, h:mm a')}
              </span>
            )}
            {assignment.points_possible && (
              <span>{assignment.points_possible} pts</span>
            )}
            {assignment.assignment_group_name && (
              <span className="hidden sm:inline">{assignment.assignment_group_name}</span>
            )}
          </div>

          {assignment.time_remaining && !assignment.submitted && (
            <p className={`text-xs font-semibold mt-1 ${
              assignment.is_overdue ? 'text-error' : assignment.is_upcoming ? 'text-gold-accent' : 'text-dark-gray'
            }`}>
              {assignment.time_remaining}
            </p>
          )}
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          {statusBadge && (
            <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${statusBadge.color}`}>
              {statusBadge.text}
            </span>
          )}
          {assignment.submitted && !assignment.graded && (
            <CheckCircle className="w-5 h-5 text-success" />
          )}
          {!assignment.submitted && assignment.submission_types?.includes('online_upload') && (
            <Link
              to={`/submit/${assignment.id}`}
              className="text-student-blue hover:text-navy-primary"
              title="Check submission"
            >
              <Upload className="w-4 h-4" />
            </Link>
          )}
          {assignment.canvas_url && (
            <a
              href={assignment.canvas_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-dark-gray hover:text-student-blue"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DeadlineDashboard() {
  const { assignments, filter, loading, syncing, overdueCount, upcomingCount, fetchAssignments, syncAssignments, setFilter } = useAssignmentStore();

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Deadlines
        </h1>
        <button
          onClick={syncAssignments}
          disabled={syncing}
          className="flex items-center gap-1.5 text-sm text-student-blue font-medium disabled:opacity-50"
        >
          {syncing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
          Sync
        </button>
      </div>

      {/* Summary Cards */}
      {(overdueCount > 0 || upcomingCount > 0) && (
        <div className="grid grid-cols-2 gap-3 mb-4">
          {overdueCount > 0 && (
            <button
              onClick={() => setFilter('overdue')}
              className={`rounded-lg p-3 text-left transition ${
                filter === 'overdue' ? 'bg-error text-white' : 'bg-error/10 text-error hover:bg-error/20'
              }`}
            >
              <AlertTriangle className="w-5 h-5 mb-1" />
              <p className="text-2xl font-bold">{overdueCount}</p>
              <p className="text-xs font-medium opacity-80">Overdue</p>
            </button>
          )}
          <button
            onClick={() => setFilter('upcoming')}
            className={`rounded-lg p-3 text-left transition ${
              filter === 'upcoming' ? 'bg-gold-accent text-white' : 'bg-gold-accent/10 text-gold-accent hover:bg-gold-accent/20'
            }`}
          >
            <Clock className="w-5 h-5 mb-1" />
            <p className="text-2xl font-bold">{upcomingCount}</p>
            <p className="text-xs font-medium opacity-80">Due Soon</p>
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-hide">
        {FILTERS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition ${
              filter === key
                ? 'bg-navy-primary text-white'
                : 'bg-white text-dark-gray hover:bg-medium-gray'
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Assignment List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-student-blue" />
        </div>
      ) : assignments.length === 0 ? (
        <div className="bg-white rounded-xl shadow-md p-8 text-center">
          <Calendar className="w-12 h-12 text-medium-gray mx-auto mb-3" />
          <h3 className="font-semibold text-dark-gray mb-1">
            {filter === 'overdue' ? 'No overdue assignments' :
             filter === 'upcoming' ? 'Nothing due soon' :
             filter === 'submitted' ? 'No submissions yet' :
             filter === 'graded' ? 'No graded assignments' :
             'No assignments found'}
          </h3>
          <p className="text-sm text-dark-gray">
            {filter === 'overdue' ? "You're all caught up!" :
             "Tap Sync to refresh from Canvas"}
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {assignments.map((a) => (
            <AssignmentCard key={a.id} assignment={a} />
          ))}
        </div>
      )}
    </div>
  );
}
