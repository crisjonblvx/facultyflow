import { create } from 'zustand';
import api from '../lib/api';
import type { GradesOverview } from '../types';

interface GradeState {
  grades: GradesOverview | null;
  loading: boolean;
  syncing: boolean;
  fetchGrades: () => Promise<void>;
  syncGrades: () => Promise<void>;
}

export const useGradeStore = create<GradeState>((set, get) => ({
  grades: null,
  loading: false,
  syncing: false,

  fetchGrades: async () => {
    set({ loading: true });
    try {
      const res = await api.get('/api/v1/student/grades');
      set({ grades: res.data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  syncGrades: async () => {
    set({ syncing: true });
    try {
      await api.post('/api/v1/student/grades/sync');
      await get().fetchGrades();
    } catch {
      // silent
    } finally {
      set({ syncing: false });
    }
  },
}));
