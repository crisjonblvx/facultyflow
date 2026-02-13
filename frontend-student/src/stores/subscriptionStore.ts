import { create } from 'zustand';
import api from '../lib/api';
import type { SubscriptionStatus } from '../types';

interface SubscriptionState {
  subscription: SubscriptionStatus | null;
  loading: boolean;
  error: string | null;

  fetchStatus: () => Promise<void>;
  createCheckout: (priceId: string, tier?: string) => Promise<string>;
  cancelSubscription: () => Promise<void>;
}

export const useSubscriptionStore = create<SubscriptionState>((set) => ({
  subscription: null,
  loading: false,
  error: null,

  fetchStatus: async () => {
    set({ loading: true, error: null });
    try {
      const res = await api.get('/api/v1/student/subscription/status');
      set({ subscription: res.data, loading: false });
    } catch {
      set({ loading: false });
    }
  },

  createCheckout: async (priceId: string, tier = 'pro') => {
    const baseUrl = window.location.origin;
    const res = await api.post('/api/stripe/create-checkout', {
      price_id: priceId,
      tier,
      success_url: `${baseUrl}/settings?upgraded=true`,
      cancel_url: `${baseUrl}/pricing`,
    });
    return res.data.checkout_url;
  },

  cancelSubscription: async () => {
    await api.post('/api/subscription/cancel');
    set((state) => ({
      subscription: state.subscription
        ? { ...state.subscription, tier: 'trial', status: 'canceled', has_pro: false }
        : null,
    }));
  },
}));
