import { create } from 'zustand';
import api from '../lib/api';
import type { FlashcardDeck, Flashcard, QuizSession, StudySchedule } from '../types';

interface StudyState {
  // Flashcards
  decks: FlashcardDeck[];
  currentCards: Flashcard[];
  decksLoading: boolean;
  cardsLoading: boolean;
  generating: boolean;

  // Quiz
  currentQuiz: QuizSession | null;
  quizLoading: boolean;

  // Study Schedule
  schedule: StudySchedule | null;
  scheduleLoading: boolean;

  // Flashcard actions
  fetchDecks: (courseId?: number) => Promise<void>;
  fetchCards: (deckId: number) => Promise<void>;
  generateFlashcards: (courseId: number, topic: string, notes: string, count?: number) => Promise<FlashcardDeck>;
  reviewCard: (cardId: number, correct: boolean) => Promise<void>;

  // Quiz actions
  generateQuiz: (courseId: number, topic: string, context?: string, numQuestions?: number) => Promise<void>;
  submitQuiz: (sessionId: number, answers: number[]) => Promise<number>;
  clearQuiz: () => void;

  // Study Schedule actions
  fetchSchedule: () => Promise<void>;
  refreshSchedule: () => Promise<void>;
}

export const useStudyStore = create<StudyState>((set, get) => ({
  decks: [],
  currentCards: [],
  decksLoading: false,
  cardsLoading: false,
  generating: false,
  currentQuiz: null,
  quizLoading: false,
  schedule: null,
  scheduleLoading: false,

  fetchDecks: async (courseId?: number) => {
    set({ decksLoading: true });
    try {
      const params = courseId ? { course_id: courseId } : {};
      const res = await api.get('/api/v1/student/flashcards/decks', { params });
      set({ decks: res.data.decks, decksLoading: false });
    } catch {
      set({ decksLoading: false });
    }
  },

  fetchCards: async (deckId: number) => {
    set({ cardsLoading: true });
    try {
      const res = await api.get(`/api/v1/student/flashcards/decks/${deckId}/cards`);
      set({ currentCards: res.data.cards, cardsLoading: false });
    } catch {
      set({ cardsLoading: false });
    }
  },

  generateFlashcards: async (courseId, topic, notes, count = 10) => {
    set({ generating: true });
    try {
      const res = await api.post('/api/v1/student/flashcards/generate', {
        course_id: courseId,
        topic,
        notes,
        card_count: count,
      });
      // Refresh decks after generation
      await get().fetchDecks();
      set({ generating: false });
      return res.data;
    } catch (err) {
      set({ generating: false });
      throw err;
    }
  },

  reviewCard: async (cardId: number, correct: boolean) => {
    try {
      await api.post('/api/v1/student/flashcards/review', {
        card_id: cardId,
        correct,
      });
      // Update local state
      set((state) => ({
        currentCards: state.currentCards.map((c) =>
          c.id === cardId
            ? {
                ...c,
                times_seen: c.times_seen + 1,
                times_correct: correct ? c.times_correct + 1 : c.times_correct,
              }
            : c
        ),
      }));
    } catch {
      // silent
    }
  },

  generateQuiz: async (courseId, topic, context = '', numQuestions = 5) => {
    set({ quizLoading: true, currentQuiz: null });
    try {
      const res = await api.post('/api/v1/student/quiz/generate', {
        course_id: courseId,
        topic,
        context,
        num_questions: numQuestions,
      });
      set({ currentQuiz: res.data, quizLoading: false });
    } catch {
      set({ quizLoading: false });
    }
  },

  submitQuiz: async (sessionId, answers) => {
    try {
      const res = await api.post('/api/v1/student/quiz/submit', {
        session_id: sessionId,
        answers,
      });
      set((state) => ({
        currentQuiz: state.currentQuiz
          ? { ...state.currentQuiz, score: res.data.score, completed_at: new Date().toISOString() }
          : null,
      }));
      return res.data.score;
    } catch {
      return 0;
    }
  },

  clearQuiz: () => set({ currentQuiz: null }),

  fetchSchedule: async () => {
    set({ scheduleLoading: true });
    try {
      const res = await api.get('/api/v1/student/study/schedule');
      set({ schedule: res.data, scheduleLoading: false });
    } catch {
      set({ scheduleLoading: false });
    }
  },

  refreshSchedule: async () => {
    set({ scheduleLoading: true });
    try {
      const res = await api.post('/api/v1/student/study/schedule/refresh');
      set({ schedule: res.data, scheduleLoading: false });
    } catch {
      set({ scheduleLoading: false });
    }
  },
}));
