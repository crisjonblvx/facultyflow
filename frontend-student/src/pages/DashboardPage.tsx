import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Bell, BookOpen, Calendar, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import { useAnnouncementStore } from '../stores/announcementStore';
import api from '../lib/api';
import type { StudentCourse } from '../types';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { unreadCount, fetchAnnouncements } = useAnnouncementStore();
  const [courses, setCourses] = useState<StudentCourse[]>([]);
  const [overdueCount, setOverdueCount] = useState(0);
  const [upcomingCount, setUpcomingCount] = useState(0);

  useEffect(() => {
    fetchAnnouncements();
    loadCourses();
    loadDeadlineCounts();
  }, [fetchAnnouncements]);

  const loadCourses = async () => {
    try {
      const res = await api.get('/api/v1/student/courses');
      setCourses(res.data.courses);
    } catch {
      // Courses not synced yet
    }
  };

  const loadDeadlineCounts = async () => {
    try {
      const [overdueRes, upcomingRes] = await Promise.all([
        api.get('/api/v1/student/assignments', { params: { filter: 'overdue', limit: 1 } }),
        api.get('/api/v1/student/assignments', { params: { filter: 'upcoming', limit: 1 } }),
      ]);
      setOverdueCount(overdueRes.data.total);
      setUpcomingCount(upcomingRes.data.total);
    } catch {
      // Not synced yet
    }
  };

  const firstName = user?.full_name?.split(' ')[0] || 'there';

  return (
    <div className="max-w-2xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-navy-primary mb-1">Hey, {firstName}</h1>
      <p className="text-dark-gray text-sm mb-6">Here's what's happening today</p>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        {/* Unread Announcements */}
        <Link
          to="/announcements"
          className="bg-white rounded-xl shadow-sm p-4 hover:shadow-md transition"
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              unreadCount > 0 ? 'bg-error/10 text-error' : 'bg-success/10 text-success'
            }`}>
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xl font-bold text-text-primary">{unreadCount}</p>
              <p className="text-[11px] text-dark-gray">Unread Alerts</p>
            </div>
          </div>
        </Link>

        {/* Deadlines */}
        <Link
          to="/deadlines"
          className="bg-white rounded-xl shadow-sm p-4 hover:shadow-md transition"
        >
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
              overdueCount > 0 ? 'bg-error/10 text-error' : 'bg-gold-accent/10 text-gold-accent'
            }`}>
              {overdueCount > 0 ? <AlertTriangle className="w-5 h-5" /> : <Calendar className="w-5 h-5" />}
            </div>
            <div>
              <p className="text-xl font-bold text-text-primary">
                {overdueCount > 0 ? overdueCount : upcomingCount}
              </p>
              <p className="text-[11px] text-dark-gray">
                {overdueCount > 0 ? 'Overdue' : 'Due Soon'}
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Courses */}
      {courses.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-text-primary mb-3 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            Your Courses
          </h2>
          <div className="space-y-2">
            {courses.map((course) => (
              <Link
                key={course.id}
                to="/grades"
                className="block bg-white rounded-lg shadow-sm p-4 hover:shadow-md transition"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-text-primary text-sm">{course.course_name}</h3>
                    <p className="text-xs text-dark-gray">{course.course_code} {course.term ? `- ${course.term}` : ''}</p>
                  </div>
                  {course.current_grade_letter && (
                    <span className="text-lg font-bold text-navy-primary">
                      {course.current_grade_letter}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {courses.length === 0 && (
        <Link
          to="/setup"
          className="block bg-student-blue/10 border-2 border-dashed border-student-blue rounded-xl p-6 text-center hover:bg-student-blue/20 transition"
        >
          <BookOpen className="w-8 h-8 text-student-blue mx-auto mb-2" />
          <p className="font-semibold text-student-blue">Connect Canvas to see your courses</p>
        </Link>
      )}
    </div>
  );
}
