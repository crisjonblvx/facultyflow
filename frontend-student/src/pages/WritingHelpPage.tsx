import { useEffect, useState } from 'react';
import { PenTool, ArrowLeft, Loader2, Sparkles, FileText, Lightbulb, MessageSquare, Shield, BookMarked } from 'lucide-react';
import api from '../lib/api';
import type { Assignment } from '../types';

const HELP_TYPES = [
  { key: 'outline', label: 'Outline', icon: <FileText className="w-4 h-4" />, desc: 'Create a structured outline' },
  { key: 'brainstorm', label: 'Brainstorm', icon: <Lightbulb className="w-4 h-4" />, desc: 'Generate ideas and angles' },
  { key: 'feedback', label: 'Feedback', icon: <MessageSquare className="w-4 h-4" />, desc: 'Review and improve your draft' },
  { key: 'strengthen', label: 'Strengthen', icon: <Shield className="w-4 h-4" />, desc: 'Make your argument stronger' },
  { key: 'cite', label: 'Citations', icon: <BookMarked className="w-4 h-4" />, desc: 'Help with sources and citations' },
];

export default function WritingHelpPage() {
  const [assignments, setAssignments] = useState<Assignment[]>([]);
  const [selectedAssignment, setSelectedAssignment] = useState<number>(0);
  const [helpType, setHelpType] = useState('outline');
  const [userInput, setUserInput] = useState('');
  const [response, setResponse] = useState('');
  const [assignmentName, setAssignmentName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadAssignments();
  }, []);

  const loadAssignments = async () => {
    try {
      const res = await api.get('/api/v1/student/assignments', { params: { filter: 'unsubmitted' } });
      setAssignments(res.data.assignments);
    } catch { /* */ }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setResponse('');

    try {
      const res = await api.post('/api/v1/student/writing/help', {
        assignment_id: selectedAssignment,
        help_type: helpType,
        user_input: userInput,
      });
      setResponse(res.data.response);
      setAssignmentName(res.data.assignment_name);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to get writing help. Try again.');
    } finally {
      setLoading(false);
    }
  };

  // ── RESPONSE VIEW ──────────────────────────────────────────
  if (response) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <button
          onClick={() => setResponse('')}
          className="flex items-center gap-1 text-sm text-dark-gray mb-4 hover:text-navy-primary transition"
        >
          <ArrowLeft className="w-4 h-4" /> Ask another question
        </button>

        <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-4 h-4 text-student-blue" />
            <span className="text-xs font-medium text-student-blue uppercase tracking-wide">
              {HELP_TYPES.find((h) => h.key === helpType)?.label} — {assignmentName}
            </span>
          </div>
          <div className="prose prose-sm max-w-none text-text-primary whitespace-pre-wrap leading-relaxed">
            {response}
          </div>
        </div>

        <div className="bg-gold-accent/10 border border-gold-accent/30 rounded-lg p-3 text-xs text-dark-gray">
          This AI assistance is meant to help you learn and improve your writing.
          Always write your own work and cite sources properly.
        </div>
      </div>
    );
  }

  // ── SETUP VIEW ─────────────────────────────────────────────
  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2 mb-1">
        <PenTool className="w-5 h-5 text-emerald-500" /> Writing Help
      </h1>
      <p className="text-dark-gray text-sm mb-6">
        AI helps you brainstorm, outline, and strengthen your writing — without doing it for you
      </p>

      {error && (
        <div className="bg-error/10 border border-error/20 text-error rounded-lg px-4 py-3 mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Assignment */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">Assignment</label>
          <select
            value={selectedAssignment}
            onChange={(e) => setSelectedAssignment(Number(e.target.value))}
            required
            className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base bg-white"
          >
            <option value={0} disabled>Select an assignment</option>
            {assignments.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} — {a.course_name}
              </option>
            ))}
          </select>
        </div>

        {/* Help Type */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">What do you need?</label>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {HELP_TYPES.map((ht) => (
              <button
                key={ht.key}
                type="button"
                onClick={() => setHelpType(ht.key)}
                className={`px-3 py-2.5 rounded-xl border-2 text-left transition text-sm ${
                  helpType === ht.key
                    ? 'border-student-blue bg-student-blue/5 text-student-blue'
                    : 'border-medium-gray text-dark-gray hover:border-student-blue/50'
                }`}
              >
                <div className="flex items-center gap-1.5 mb-0.5">
                  {ht.icon}
                  <span className="font-semibold text-xs">{ht.label}</span>
                </div>
                <p className="text-[10px] leading-tight opacity-70">{ht.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* User Input */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-1">
            {helpType === 'outline' && 'What is your paper about?'}
            {helpType === 'brainstorm' && 'What topic do you want ideas for?'}
            {helpType === 'feedback' && 'Paste your draft below'}
            {helpType === 'strengthen' && 'Paste the section to strengthen'}
            {helpType === 'cite' && 'What do you need help citing?'}
          </label>
          <textarea
            value={userInput}
            onChange={(e) => setUserInput(e.target.value)}
            required
            rows={6}
            placeholder={
              helpType === 'feedback' || helpType === 'strengthen'
                ? 'Paste your writing here...'
                : 'Describe what you need help with...'
            }
            className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base resize-none"
          />
        </div>

        <button
          type="submit"
          disabled={loading || !selectedAssignment || !userInput}
          className="w-full bg-navy-primary text-white py-3 rounded-lg font-semibold hover:bg-navy-hover transition disabled:opacity-50 min-h-[48px] flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Thinking...
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              Get Writing Help
            </>
          )}
        </button>
      </form>
    </div>
  );
}
