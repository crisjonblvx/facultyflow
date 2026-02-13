import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FileText, Film, Upload, CheckCircle, AlertTriangle, XCircle, ArrowLeft, Loader2 } from 'lucide-react';
import api from '../lib/api';
import { format } from 'date-fns';
import type { Assignment, ValidationResult } from '../types';

export default function SubmissionChecker() {
  const { assignmentId } = useParams();
  const navigate = useNavigate();
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (assignmentId) {
      loadAssignment();
    }
  }, [assignmentId]);

  const loadAssignment = async () => {
    try {
      const res = await api.get(`/api/v1/student/assignments/${assignmentId}`);
      setAssignment(res.data);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (selectedFile: File) => {
    setFile(selectedFile);
    setValidation(null);
    setValidating(true);

    try {
      const res = await api.post('/api/v1/student/submissions/validate', null, {
        params: {
          assignment_id: assignmentId,
          file_name: selectedFile.name,
          file_size: selectedFile.size,
        },
      });
      setValidation(res.data);
    } catch {
      setValidation({
        is_valid: false,
        issues: ['Could not validate file'],
        suggestions: ['Try again or contact support'],
        warnings: [],
        can_auto_fix: false,
        auto_fix_options: [],
      });
    } finally {
      setValidating(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const dropped = e.dataTransfer.files[0];
    if (dropped) handleFileSelect(dropped);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const isVideo = file && /\.(mp4|mov|avi|mkv|wmv|webm)$/i.test(file.name);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-student-blue" />
      </div>
    );
  }

  if (!assignment) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6 text-center">
        <p className="text-dark-gray">Assignment not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-sm text-student-blue font-medium mb-4"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      {/* Assignment Info */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-4">
        <p className="text-xs font-medium text-student-blue">{assignment.course_name}</p>
        <h1 className="text-lg font-bold text-text-primary mt-1">{assignment.name}</h1>
        <div className="flex items-center gap-4 mt-2 text-xs text-dark-gray">
          {assignment.points_possible && <span>{assignment.points_possible} points</span>}
          {assignment.due_at && (
            <span className={assignment.is_overdue ? 'text-error font-semibold' : ''}>
              Due {format(new Date(assignment.due_at), 'MMM d, h:mm a')}
              {assignment.is_overdue && ' (Overdue!)'}
              {assignment.time_remaining && !assignment.is_overdue && ` (${assignment.time_remaining})`}
            </span>
          )}
        </div>
        {assignment.allowed_file_types && assignment.allowed_file_types.length > 0 && (
          <p className="text-xs text-dark-gray mt-2">
            Accepted: {assignment.allowed_file_types.map(t => t.toUpperCase().replace('.', '')).join(', ')}
          </p>
        )}
      </div>

      {/* File Upload Area */}
      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        className="bg-white rounded-xl shadow-sm border-2 border-dashed border-medium-gray hover:border-student-blue transition p-6 text-center mb-4"
      >
        {!file ? (
          <>
            <Upload className="w-10 h-10 text-medium-gray mx-auto mb-3" />
            <p className="font-medium text-text-primary mb-1">Drop your file here</p>
            <p className="text-sm text-dark-gray mb-3">or</p>
            <label className="inline-block bg-student-blue text-white px-6 py-2.5 rounded-lg font-medium cursor-pointer hover:bg-student-blue/90 transition">
              Browse Files
              <input
                type="file"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
              />
            </label>
          </>
        ) : (
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-light-gray rounded-lg flex items-center justify-center">
              {isVideo ? <Film className="w-6 h-6 text-student-blue" /> : <FileText className="w-6 h-6 text-student-blue" />}
            </div>
            <div className="flex-1 text-left">
              <p className="font-medium text-text-primary text-sm truncate">{file.name}</p>
              <p className="text-xs text-dark-gray">{formatFileSize(file.size)}</p>
            </div>
            <button
              onClick={() => { setFile(null); setValidation(null); }}
              className="text-dark-gray hover:text-error text-sm font-medium"
            >
              Remove
            </button>
          </div>
        )}
      </div>

      {/* Validation Results */}
      {validating && (
        <div className="bg-white rounded-xl shadow-sm p-6 flex items-center justify-center gap-3">
          <Loader2 className="w-5 h-5 animate-spin text-student-blue" />
          <span className="text-sm text-dark-gray">Checking your file...</span>
        </div>
      )}

      {validation && !validating && (
        <div className={`rounded-xl shadow-sm p-5 border-2 ${
          validation.is_valid ? 'bg-success/5 border-success' : 'bg-error/5 border-error'
        }`}>
          <div className="flex items-center gap-3 mb-3">
            {validation.is_valid ? (
              <>
                <CheckCircle className="w-8 h-8 text-success" />
                <div>
                  <h3 className="font-bold text-success">Ready to submit!</h3>
                  <p className="text-xs text-dark-gray">Your file passed all checks.</p>
                </div>
              </>
            ) : (
              <>
                <AlertTriangle className="w-8 h-8 text-error" />
                <div>
                  <h3 className="font-bold text-error">Issues found</h3>
                  <p className="text-xs text-dark-gray">Fix these before submitting.</p>
                </div>
              </>
            )}
          </div>

          {/* Issues */}
          {validation.issues.length > 0 && (
            <div className="space-y-2 mb-3">
              {validation.issues.map((issue, i) => (
                <div key={i} className="flex items-start gap-2 text-sm">
                  <XCircle className="w-4 h-4 text-error mt-0.5 shrink-0" />
                  <span className="text-text-primary">{issue}</span>
                </div>
              ))}
            </div>
          )}

          {/* Suggestions */}
          {validation.suggestions.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold text-dark-gray mb-1">How to fix:</p>
              <ul className="space-y-1">
                {validation.suggestions.map((s, i) => (
                  <li key={i} className="text-sm text-dark-gray flex items-start gap-2">
                    <span className="text-student-blue">-</span> {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Warnings */}
          {validation.warnings.length > 0 && (
            <div className="mt-3 bg-gold-accent/10 rounded-lg p-3">
              {validation.warnings.map((w, i) => (
                <p key={i} className="text-sm text-gold-accent flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" /> {w}
                </p>
              ))}
            </div>
          )}

          {/* Submit Button */}
          {validation.is_valid && (
            <a
              href={assignment.canvas_url || '#'}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 w-full bg-success text-white py-3 rounded-lg font-semibold text-center block hover:bg-success/90 transition"
            >
              Open in Canvas to Submit
            </a>
          )}
        </div>
      )}
    </div>
  );
}
