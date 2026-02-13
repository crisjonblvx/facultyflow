import { create } from 'zustand';
import api from '../lib/api';
import type { User } from '../types';

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;

  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  loadFromStorage: () => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isAuthenticated: false,
  loading: false,
  error: null,

  login: async (email: string, password: string) => {
    set({ loading: true, error: null });
    try {
      const response = await api.post('/api/auth/login', { email, password });
      const { token, user } = response.data;

      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));

      set({ token, user, isAuthenticated: true, loading: false });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      set({ error: message, loading: false });
      throw new Error(message);
    }
  },

  register: async (email: string, password: string, fullName: string) => {
    set({ loading: true, error: null });
    try {
      const response = await api.post('/api/auth/register', {
        email,
        password,
        full_name: fullName,
      });
      const { token, user } = response.data;

      localStorage.setItem('auth_token', token);
      localStorage.setItem('user', JSON.stringify(user));

      set({ token, user, isAuthenticated: true, loading: false });
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Registration failed';
      set({ error: message, loading: false });
      throw new Error(message);
    }
  },

  logout: () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    set({ token: null, user: null, isAuthenticated: false });
  },

  loadFromStorage: () => {
    const token = localStorage.getItem('auth_token');
    const userStr = localStorage.getItem('user');
    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        set({ token, user, isAuthenticated: true });
      } catch {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user');
      }
    }
  },

  clearError: () => set({ error: null }),
}));
