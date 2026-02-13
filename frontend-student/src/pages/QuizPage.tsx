import { useEffect, useState } from 'react';
import { Brain, ArrowLeft, Loader2, CheckCircle, XCircle, Trophy } from 'lucide-react';
import { useStudyStore } from '../stores/studyStore';
import api from '../lib/api';
import type { StudentCourse } from '../types';

type View = 'setup' | 'quiz' | 'results';

export default function QuizPage() {
  const { currentQuiz, quizLoading, generateQuiz, submitQuiz, clearQuiz } = useStudyStore();
  const [view, setView] = useState<View>('setup');
  const [courses, setCourses] = useState<StudentCourse[]>([]);

  // Setup
  const [selectedCourse, setSelectedCourse] = useState<number>(0);
  const [topic, setTopic] = useState('');
  const [context, setContext] = useState('');
  const [numQuestions, setNumQuestions] = useState(5);

  // Quiz
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [showExplanation, setShowExplanation] = useState(false);

  // Results
  const [score, setScore] = useState(0);

  useEffect(() => {
    loadCourses();
    return () => clearQuiz();
  }, [clearQuiz]);

  const loadCourses = async () => {
    try {
      const res = await api.get('/api/v1/student/courses');
      setCourses(res.data.courses);
    } catch { /* */ }
  };

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    await generateQuiz(selectedCourse, topic, context, numQuestions);
    setAnswers(new Array(numQuestions).fill(null));
    setCurrentQ(0);
    setShowExplanation(false);
    setView('quiz');
  };

  const selectAnswer = (optionIndex: number) => {
    if (showExplanation) return;
    const newAnswers = [...answers];
    newAnswers[currentQ] = optionIndex;
    setAnswers(newAnswers);
    setShowExplanation(true);
  };

  const nextQuestion = () => {
    setShowExplanation(false);
    if (currentQ < (currentQuiz?.questions.length || 0) - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      finishQuiz();
    }
  };

  const finishQuiz = async () => {
    if (!currentQuiz) return;
    const finalAnswers = answers.map((a) => a ?? -1);
    const s = await submitQuiz(currentQuiz.id, finalAnswers);
    setScore(s);
    setView('results');
  };

  const question = currentQuiz?.questions[currentQ];
  const totalQuestions = currentQuiz?.questions.length || 0;

  // ── SETUP ───────────────────────────────────────────────────
  if (view === 'setup') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <h1 className="text-xl font-bold text-navy-primary flex items-center gap-2 mb-6">
          <Brain className="w-5 h-5 text-student-blue" /> Quiz Yourself
        </h1>

        <div className="bg-student-blue/5 border border-student-blue/20 rounded-lg p-4 mb-6">
          <p className="text-sm text-navy-primary">
            AI generates practice questions based on your topic and notes. Great for testing what you know before an exam.
          </p>
        </div>

        <form onSubmit={handleGenerate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Course</label>
            <select
              value={selectedCourse}
              onChange={(e) => setSelectedCourse(Number(e.target.value))}
              required
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base bg-white"
            >
              <option value={0} disabled>Select a course</option>
              {courses.map((c) => (
                <option key={c.id} value={c.id}>{c.course_name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">Topic</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              required
              placeholder="e.g., Photosynthesis, Civil War, Calculus Limits"
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Study Notes (optional — improves question quality)
            </label>
            <textarea
              value={context}
              onChange={(e) => setContext(e.target.value)}
              rows={5}
              placeholder="Paste relevant notes, lecture content, or textbook excerpts to generate more targeted questions."
              className="w-full px-4 py-3 border border-medium-gray rounded-lg focus:ring-2 focus:ring-student-blue focus:border-transparent outline-none text-base resize-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-1">
              Questions: {numQuestions}
            </label>
            <input
              type="range"
              min={3}
              max={10}
              value={numQuestions}
              onChange={(e) => setNumQuestions(Number(e.target.value))}
              className="w-full accent-student-blue"
            />
            <div className="flex justify-between text-xs text-dark-gray">
              <span>3</span>
              <span>10</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={quizLoading || !selectedCourse || !topic}
            className="w-full bg-navy-primary text-white py-3 rounded-lg font-semibold hover:bg-navy-hover transition disabled:opacity-50 min-h-[48px] flex items-center justify-center gap-2"
          >
            {quizLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating quiz...
              </>
            ) : (
              <>
                <Brain className="w-4 h-4" />
                Start Quiz
              </>
            )}
          </button>
        </form>
      </div>
    );
  }

  // ── QUIZ ────────────────────────────────────────────────────
  if (view === 'quiz' && question) {
    const isCorrect = answers[currentQ] === question.correct_index;
    const progressPct = ((currentQ + 1) / totalQuestions) * 100;

    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm text-dark-gray font-medium">
            Question {currentQ + 1} of {totalQuestions}
          </span>
          <span className="text-sm text-dark-gray">
            {answers.filter((a, i) => a === currentQuiz?.questions[i]?.correct_index).length} correct
          </span>
        </div>

        {/* Progress */}
        <div className="h-1.5 bg-medium-gray rounded-full mb-6 overflow-hidden">
          <div
            className="h-full bg-student-blue rounded-full transition-all duration-300"
            style={{ width: `${progressPct}%` }}
          />
        </div>

        {/* Question */}
        <div className="bg-white rounded-xl shadow-sm p-5 mb-4">
          <p className="font-semibold text-text-primary text-base leading-relaxed">
            {question.question}
          </p>
        </div>

        {/* Options */}
        <div className="space-y-2">
          {question.options.map((opt, i) => {
            let optionStyle = 'bg-white border-medium-gray hover:border-student-blue';
            if (showExplanation) {
              if (i === question.correct_index) {
                optionStyle = 'bg-success/10 border-success';
              } else if (i === answers[currentQ] && !isCorrect) {
                optionStyle = 'bg-error/10 border-error';
              } else {
                optionStyle = 'bg-white border-medium-gray opacity-50';
              }
            } else if (answers[currentQ] === i) {
              optionStyle = 'bg-student-blue/10 border-student-blue';
            }

            return (
              <button
                key={i}
                onClick={() => selectAnswer(i)}
                disabled={showExplanation}
                className={`w-full text-left px-4 py-3 rounded-xl border-2 transition text-sm font-medium ${optionStyle}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-7 h-7 rounded-full bg-light-gray flex items-center justify-center text-xs font-bold text-dark-gray shrink-0">
                    {String.fromCharCode(65 + i)}
                  </span>
                  <span className="text-text-primary">{opt}</span>
                  {showExplanation && i === question.correct_index && (
                    <CheckCircle className="w-5 h-5 text-success ml-auto shrink-0" />
                  )}
                  {showExplanation && i === answers[currentQ] && !isCorrect && (
                    <XCircle className="w-5 h-5 text-error ml-auto shrink-0" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        {/* Explanation */}
        {showExplanation && (
          <div className={`mt-4 p-4 rounded-xl text-sm ${isCorrect ? 'bg-success/10 border border-success/20' : 'bg-error/10 border border-error/20'}`}>
            <p className="font-semibold mb-1">
              {isCorrect ? 'Correct!' : 'Not quite.'}
            </p>
            <p className="text-dark-gray">{question.explanation}</p>
          </div>
        )}

        {showExplanation && (
          <button
            onClick={nextQuestion}
            className="w-full mt-4 bg-student-blue text-white py-3 rounded-lg font-semibold hover:bg-student-blue/90 transition min-h-[48px]"
          >
            {currentQ < totalQuestions - 1 ? 'Next Question' : 'See Results'}
          </button>
        )}
      </div>
    );
  }

  // ── RESULTS ─────────────────────────────────────────────────
  if (view === 'results') {
    const pct = totalQuestions > 0 ? Math.round((score / totalQuestions) * 100) : 0;
    const emoji = pct >= 80 ? 'text-success' : pct >= 60 ? 'text-gold-accent' : 'text-error';

    return (
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <Trophy className={`w-16 h-16 mx-auto mb-4 ${emoji}`} />
          <h2 className="text-2xl font-bold text-navy-primary mb-2">Quiz Complete!</h2>
          <p className="text-4xl font-black text-text-primary mb-1">
            {score} / {totalQuestions}
          </p>
          <p className={`text-lg font-semibold ${emoji}`}>{pct}%</p>
          <p className="text-dark-gray text-sm mt-2">
            {pct >= 80 ? 'Great job! You know this material well.' :
             pct >= 60 ? 'Good effort! Review the topics you missed.' :
             'Keep studying — you\'ll get there!'}
          </p>

          <div className="flex gap-3 mt-6">
            <button
              onClick={() => {
                clearQuiz();
                setView('setup');
                setCurrentQ(0);
                setShowExplanation(false);
              }}
              className="flex-1 bg-student-blue text-white py-3 rounded-lg font-semibold hover:bg-student-blue/90 transition"
            >
              New Quiz
            </button>
            <button
              onClick={() => {
                setCurrentQ(0);
                setShowExplanation(false);
                setAnswers(new Array(totalQuestions).fill(null));
                setView('quiz');
              }}
              className="flex-1 border-2 border-student-blue text-student-blue py-3 rounded-lg font-semibold hover:bg-student-blue/5 transition"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Fallback loading
  return (
    <div className="flex justify-center py-16">
      <Loader2 className="w-6 h-6 animate-spin text-student-blue" />
    </div>
  );
}
