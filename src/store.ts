import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { playAlertSound } from './utils/mockDataGenerator';

export interface Transaction {
  id: string;
  userId: string;
  amount: number;
  location: string;
  category: string;
  timestamp: number;
  riskScore: number;
  isFraud: boolean;
  status: 'safe' | 'suspicious' | 'fraud' | 'completed' | 'refunded' | 'pending';
  flagReason?: string;
  lat: number;
  lng: number;
  payment_status?: string;
  payment_id?: string;
  razorpay_order_id?: string;
  refund_status?: string;
  refund_id?: string;
  target_account?: string;
  device_id?: string;
}

export type UserRole = 'admin' | 'user' | null;

interface AppState {
  // Auth State
  currentUser: { id: string; name: string; role: UserRole; bankConnected?: boolean } | null;
  users: Record<string, { id: string; pin: string }>;
  
  
  // App State
  transactions: Transaction[];
  alertTransaction: Transaction | null;
  soundEnabled: boolean;
  simulationActive: boolean;
  fraudSensitivity: number;
  transactionLimit: number;
  
  // Geolocation & Localization
  userLocation: { city: string; country: string } | null;
  userCurrency: string; // e.g. USD, EUR, INR

  // Living Balance
  userBalance: number;

  // Actions
  login: (role: UserRole, name: string) => void;
  logout: () => void;
  initLocation: () => Promise<void>;
  adjustBalance: (amount: number) => void;
  connectBank: (balance: number) => void;
  addTransaction: (tx: Transaction) => void;
  setAlertTransaction: (tx: Transaction | null) => void;
  setTransactionLimit: (limit: number) => void;
  toggleSound: () => void;
  toggleSimulation: () => void;
  setFraudSensitivity: (level: number) => void;
  markAsSafe: (id: string) => void;
  blockTransaction: (id: string) => void;
  updateTransaction: (tx: Transaction) => void;
  setPin: (pin: string) => void;
}

const initialTransactions: Transaction[] = [];

export const useStore = create<AppState>()(
  persist(
    (set, get) => ({
  currentUser: null,
  users: {},
  transactions: initialTransactions,
  alertTransaction: null,
  soundEnabled: true,
  simulationActive: true,
  fraudSensitivity: 5,
  transactionLimit: 5000,
  userLocation: null,
  userCurrency: 'USD',
  userBalance: 0, // Starts at 0 until bank connects
  
  login: (role, name) => set((state) => {
    let userRecord = state.users?.[name];
    const newUsers = { ...(state.users || {}) };
    if (!userRecord) {
       userRecord = { id: 'usr_' + Math.random().toString(36).substring(2,8), pin: '1234' };
       newUsers[name] = userRecord;
    }
    return {
       users: newUsers,
       currentUser: { id: userRecord.id, name, role, bankConnected: role === 'admin' }
    };
  }),
  logout: () => set({ currentUser: null }),
  
  setPin: (pin) => set((state) => {
    if (!state.currentUser) return {};
    const name = state.currentUser.name;
    return {
      users: {
        ...(state.users || {}),
        [name]: { ...(state.users?.[name]), pin }
      }
    };
  }),
  
  initLocation: async () => {
    try {
      const res = await fetch('https://ipapi.co/json/');
      const data = await res.json();
      if (data && data.currency) {
        set({ 
          userLocation: { city: data.city, country: data.country_name },
          userCurrency: data.currency 
        });
      }
    } catch(e) {
      console.error("Failed to fetch location", e);
    }
  },

  adjustBalance: (amount) => set((state) => ({ userBalance: state.userBalance + amount })),

  connectBank: (balance) => set((state) => ({
    userBalance: balance,
    currentUser: state.currentUser ? { ...state.currentUser, bankConnected: true } : null
  })),

  addTransaction: (tx) => set((state) => ({ 
    transactions: [tx, ...state.transactions].slice(0, 150)
  })),
  
  setAlertTransaction: (tx) => {
    set({ alertTransaction: tx });
    if (tx && tx.isFraud && get().soundEnabled) {
      playAlertSound();
    }
  },

  setTransactionLimit: (limit) => set({ transactionLimit: limit }),
  
  toggleSound: () => set((state) => ({ soundEnabled: !state.soundEnabled })),
  toggleSimulation: () => set((state) => ({ simulationActive: !state.simulationActive })),
  setFraudSensitivity: (level) => set({ fraudSensitivity: level }),
  
  markAsSafe: (id) => set((state) => ({
    transactions: state.transactions.map(t => 
      t.id === id ? { ...t, status: 'safe', isFraud: false, riskScore: Math.min(t.riskScore, 30) } : t
    ),
    alertTransaction: null
  })),
  
  blockTransaction: (id) => set((state) => ({
    transactions: state.transactions.map(t => 
      t.id === id ? { ...t, status: 'fraud', isFraud: true } : t
    ),
    alertTransaction: null
  })),
  
  updateTransaction: (tx) => set((state) => {
    const exists = state.transactions.some(t => t.id === tx.id);
    if(exists) {
      return { transactions: state.transactions.map(t => t.id === tx.id ? tx : t) };
    }
    return { transactions: [tx, ...state.transactions].slice(0, 150) };
  })
    }),
    {
      name: 'fraudshield-store',
      partialize: (state: AppState) => ({
        currentUser: state.currentUser,
        users: state.users,
        transactions: state.transactions,
        userLocation: state.userLocation,
        userCurrency: state.userCurrency,
        userBalance: state.userBalance,
        soundEnabled: state.soundEnabled,
        fraudSensitivity: state.fraudSensitivity,
        transactionLimit: state.transactionLimit,
        simulationActive: state.simulationActive
      })
    }
  )
);
