import { create } from 'zustand';
import api from '../lib/api';
import type { Assignment, AssignmentFilter } from '../types';

interface AssignmentState {
  assignments: Assignment[];
  filter: AssignmentFilter;
  loading: boolean;
  syncing: boolean;
  total: number;
  overdueCount: number;
  upcomingCount: number;
  fetchAssignments: () => Promise<void>;
  syncAssignments: () => Promise<void>;
  setFilter: (filter: AssignmentFilter) => void;
}

export const useAssignmentStore = create<AssignmentState>((set, get) => ({
  assignments: [],
  filter: 'upcoming',
  loading: false,
  syncing: false,
  total: 0,
  overdueCount: 0,
  upcomingCount: 0,

  fetchAssignments: async () => {
    set({ loading: true });
    try {
      const { filter } = get();
      const res = await api.get('/api/v1/student/assignments', {
        params: { filter, sort: 'due_date', limit: 100 },
      });
      const assignments = res.data.assignments;

      // Also fetch counts for overdue/upcoming badges
      const [overdueRes, upcomingRes] = await Promise.all([
        api.get('/api/v1/student/assignments', { params: { filter: 'overdue', limit: 1 } }),
        api.get('/api/v1/student/assignments', { params: { filter: 'upcoming', limit: 1 } }),
      ]);

      set({
        assignments,
        total: res.data.total,
        overdueCount: overdueRes.data.total,
        upcomingCount: upcomingRes.data.total,
        loading: false,
      });
    } catch {
      set({ loading: false });
    }
  },

  syncAssignments: async () => {
    set({ syncing: true });
    try {
      await api.post('/api/v1/student/assignments/sync');
      await get().fetchAssignments();
    } catch {
      // silent
    } finally {
      set({ syncing: false });
    }
  },

  setFilter: (filter: AssignmentFilter) => {
    set({ filter });
    get().fetchAssignments();
  },
}));
