import { Link } from 'react-router-dom';
import { Brain, BookOpen, PenTool, CalendarClock, Sparkles } from 'lucide-react';

const tools = [
  {
    to: '/study/flashcards',
    icon: <BookOpen className="w-7 h-7" />,
    color: 'bg-violet-500',
    title: 'Flashcards',
    desc: 'Generate study cards from your notes with AI',
  },
  {
    to: '/study/quiz',
    icon: <Brain className="w-7 h-7" />,
    color: 'bg-student-blue',
    title: 'Quiz Yourself',
    desc: 'AI-generated practice quizzes on any topic',
  },
  {
    to: '/study/writing',
    icon: <PenTool className="w-7 h-7" />,
    color: 'bg-emerald-500',
    title: 'Writing Help',
    desc: 'Get feedback, outlines, and brainstorming help',
  },
  {
    to: '/study/schedule',
    icon: <CalendarClock className="w-7 h-7" />,
    color: 'bg-gold-accent',
    title: 'Study Schedule',
    desc: 'AI-built daily plan based on your deadlines',
  },
];

export default function StudyHubPage() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <div className="flex items-center gap-2 mb-1">
        <Sparkles className="w-5 h-5 text-student-blue" />
        <h1 className="text-2xl font-bold text-navy-primary">Study Tools</h1>
      </div>
      <p className="text-dark-gray text-sm mb-6">AI-powered tools to help you study smarter</p>

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
