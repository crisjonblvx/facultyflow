import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './stores/authStore';

import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import CanvasSetupPage from './pages/CanvasSetupPage';
import DashboardPage from './pages/DashboardPage';
import AnnouncementHub from './pages/AnnouncementHub';
import DeadlineDashboard from './pages/DeadlineDashboard';
import GradesPage from './pages/GradesPage';
import SubmissionChecker from './pages/SubmissionChecker';
import SettingsPage from './pages/SettingsPage';
import StudyHubPage from './pages/StudyHubPage';
import FlashcardsPage from './pages/FlashcardsPage';
import QuizPage from './pages/QuizPage';
import WritingHelpPage from './pages/WritingHelpPage';
import StudySchedulePage from './pages/StudySchedulePage';
import PricingPage from './pages/PricingPage';
import LandingPage from './pages/LandingPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  const { loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        {/* Canvas setup (auth required but no bottom nav) */}
        <Route
          path="/setup"
          element={
            <ProtectedRoute>
              <CanvasSetupPage />
            </ProtectedRoute>
          }
        />

        {/* App routes with Layout (header + bottom nav) */}
        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/announcements" element={<AnnouncementHub />} />
          <Route path="/deadlines" element={<DeadlineDashboard />} />
          <Route path="/grades" element={<GradesPage />} />
          <Route path="/submit/:assignmentId" element={<SubmissionChecker />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/pricing" element={<PricingPage />} />

          {/* AI Study Tools */}
          <Route path="/study" element={<StudyHubPage />} />
          <Route path="/study/flashcards" element={<FlashcardsPage />} />
          <Route path="/study/quiz" element={<QuizPage />} />
          <Route path="/study/writing" element={<WritingHelpPage />} />
          <Route path="/study/schedule" element={<StudySchedulePage />} />
        </Route>

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
