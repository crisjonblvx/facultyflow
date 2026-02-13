import { create } from 'zustand';
import api from '../lib/api';
import type { Announcement, AnnouncementFilter } from '../types';

interface AnnouncementState {
  announcements: Announcement[];
  unreadCount: number;
  total: number;
  filter: AnnouncementFilter;
  loading: boolean;
  syncing: boolean;
  error: string | null;

  fetchAnnouncements: () => Promise<void>;
  syncAnnouncements: () => Promise<{ new_count: number }>;
  markAsRead: (id: number) => Promise<void>;
  togglePin: (id: number, pinned: boolean) => Promise<void>;
  markAllRead: (courseId?: number) => Promise<void>;
  setFilter: (filter: AnnouncementFilter) => void;
}

export const useAnnouncementStore = create<AnnouncementState>((set, get) => ({
  announcements: [],
  unreadCount: 0,
  total: 0,
  filter: 'all',
  loading: false,
  syncing: false,
  error: null,

  fetchAnnouncements: async () => {
    set({ loading: true, error: null });
    try {
      const { filter } = get();
      const response = await api.get('/api/v1/student/announcements', {
        params: { filter, limit: 100 },
      });
      set({
        announcements: response.data.announcements,
        unreadCount: response.data.unread_count,
        total: response.data.total,
        loading: false,
      });
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Failed to load announcements', loading: false });
    }
  },

  syncAnnouncements: async () => {
    set({ syncing: true, error: null });
    try {
      const response = await api.post('/api/v1/student/announcements/sync');
      // Refresh list after sync
      await get().fetchAnnouncements();
      set({ syncing: false });
      return response.data;
    } catch (err: any) {
      set({ error: err.response?.data?.detail || 'Sync failed', syncing: false });
      return { new_count: 0 };
    }
  },

  markAsRead: async (id: number) => {
    try {
      await api.post(`/api/v1/student/announcements/${id}/read`);
      set((state) => ({
        announcements: state.announcements.map((a) =>
          a.id === id ? { ...a, read_status: true } : a
        ),
        unreadCount: Math.max(0, state.unreadCount - 1),
      }));
    } catch (err: any) {
      console.error('Failed to mark as read:', err);
    }
  },

  togglePin: async (id: number, pinned: boolean) => {
    try {
      await api.post(`/api/v1/student/announcements/${id}/pin`, { pinned: !pinned });
      set((state) => ({
        announcements: state.announcements.map((a) =>
          a.id === id ? { ...a, pinned: !pinned } : a
        ),
      }));
    } catch (err: any) {
      console.error('Failed to toggle pin:', err);
    }
  },

  markAllRead: async (courseId?: number) => {
    try {
      await api.post('/api/v1/student/announcements/mark-all-read', {
        course_id: courseId || null,
      });
      set((state) => ({
        announcements: state.announcements.map((a) => ({ ...a, read_status: true })),
        unreadCount: 0,
      }));
    } catch (err: any) {
      console.error('Failed to mark all as read:', err);
    }
  },

  setFilter: (filter: AnnouncementFilter) => {
    set({ filter });
  },
}));
