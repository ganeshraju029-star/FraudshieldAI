import { Transaction, useStore } from '../store';

export const LOCATIONS = [
  { name: 'New York, USA', lat: 40.7128, lng: -74.0060 },
  { name: 'London, UK', lat: 51.5074, lng: -0.1278 },
  { name: 'Tokyo, Japan', lat: 35.6762, lng: 139.6503 },
  { name: 'Lagos, Nigeria', lat: 6.5244, lng: 3.3792 },
  { name: 'São Paulo, Brazil', lat: -23.5505, lng: -46.6333 },
  { name: 'Moscow, Russia', lat: 55.7558, lng: 37.6173 },
  { name: 'Sydney, Australia', lat: -33.8688, lng: 151.2093 }
];

export const CATEGORIES = ['Retail', 'Digital Goods', 'Crypto', 'Travel', 'P2P Transfer', 'Gambling', 'Groceries'];

const generateId = () => Math.random().toString(36).substring(2, 10);

export const evaluateFraudRisk = (amount: number, location: string, category: string, forceFraud: boolean = false) => {
  const isFraud = forceFraud || Math.random() < 0.05; // 5% base chance of fraud or forced
  const riskScore = isFraud ? Math.floor(Math.random() * 20) + 80 : Math.floor(Math.random() * 40);
  
  let flagReason = '';
  if (isFraud) {
    const reasons = ['Unusual Location', 'High Amount Deviation', 'New Merchant Category', 'Velocity Mismatch'];
    flagReason = reasons[Math.floor(Math.random() * reasons.length)];
  }

  return { isFraud, riskScore, flagReason };
};

export const generateMockTransaction = (forceFraud: boolean = false): Transaction => {
  const location = LOCATIONS[Math.floor(Math.random() * LOCATIONS.length)];
  const isFraudBase = forceFraud || Math.random() < 0.05; 
  const amount = isFraudBase ? Math.floor(Math.random() * 50000) + 5000 : Math.floor(Math.random() * 500) + 10;
  const category = CATEGORIES[Math.floor(Math.random() * CATEGORIES.length)];
  
  const { isFraud, riskScore, flagReason } = evaluateFraudRisk(amount, location.name, category, forceFraud);

  return {
    id: `tx_${generateId()}`,
    userId: `usr_${generateId()}`,
    amount,
    location: location.name,
    lat: location.lat,
    lng: location.lng,
    category,
    timestamp: Date.now(),
    riskScore,
    isFraud,
    status: isFraud ? 'fraud' : (riskScore > 30 ? 'suspicious' : 'safe'),
    flagReason: isFraud ? flagReason : undefined
  };
};

let socketInst: WebSocket | null = null;

export const startSimulation = () => {
  if (socketInst) return;
  socketInst = new WebSocket('ws://dummy'); // temporary lock
  
  // Pre-fill some transactions from the backend
  fetch('/api/transactions')
    .then(res => res.json())
    .then(data => {
      if (data.transactions) {
        // Since addTransaction prepends, let's reverse to keep chronological order
        [...data.transactions].reverse().forEach(tx => {
          useStore.getState().addTransaction(tx);
        });
      }
    })
    .catch(e => {
        console.error("Failed to fetch initial transactions, generating mocks", e);
        for (let i = 0; i < 20; i++) {
          useStore.getState().addTransaction(generateMockTransaction());
        }
    });

  const connect = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const token = localStorage.getItem('token');
    const wsUrl = token 
        ? `${protocol}//${window.location.host}/ws/stream?token=${token}` 
        : `${protocol}//${window.location.host}/ws/stream`;
    socketInst = new WebSocket(wsUrl);
    
    socketInst.onmessage = (event) => {
      const state = useStore.getState();
      if (!state.simulationActive) return;

      try {
        const msg = JSON.parse(event.data);
        if (['transaction', 'payment_completed', 'payment_refunded', 'fraud_alert'].includes(msg.type)) {
          // Add or update the transaction locally
          useStore.getState().updateTransaction(msg.data);

          // Pop alert if requested (high risk + not already alerted)
          if ((msg.type === 'fraud_alert' || (msg.data.isFraud && msg.data.riskScore > 80)) && !useStore.getState().alertTransaction) {
            const isTargetUser = state.currentUser?.id === msg.data.userId;
            const isAdmin = state.currentUser?.role === 'admin';
            
            if (isAdmin || isTargetUser) {
              useStore.getState().setAlertTransaction(msg.data);
            }
          }
        }
      } catch (e) {
        console.error("Error parsing WS message", e);
      }
    };

    socketInst.onclose = () => {
      setTimeout(connect, 3000);
    };
  };

  connect();

  // --- Client-Side Simulation Fallback ---
  // If the WebSocket is not open (common on Netlify), generate mock data locally 
  // every 7 seconds to keep the 'Live Feed' and 'Alerts' alive.
  setInterval(() => {
    const state = useStore.getState();
    if (!state.simulationActive) return;

    // Only simulate locally if the socket is NOT open
    if (!socketInst || socketInst.readyState !== WebSocket.OPEN) {
      // For the demo, provide a steady stream of background transactions
      const isDemoFraud = Math.random() < 0.15; // Reduced fraud probability for background noise
      const mockTx = generateMockTransaction(isDemoFraud);
      state.addTransaction(mockTx);

      // Automated alerts are disabled per user request to only show on manual transactions.
      // Logic for manual transaction alerts remains in UserDashboard.tsx
    }
  }, 10000); // Slower 10-second interval for background feed
};

let audioCtx: AudioContext | null = null;

export const initAudio = () => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
};

export const playAlertSound = () => {
  try {
    if (!audioCtx) {
      initAudio();
    }
    if (!audioCtx) return;

    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
    
    const now = audioCtx.currentTime;
    
    const playBeep = (freq: number, start: number, duration: number) => {
      const osc = audioCtx!.createOscillator();
      const gain = audioCtx!.createGain();
      
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, start);
      osc.frequency.exponentialRampToValueAtTime(freq * 0.8, start + duration);
      
      gain.gain.setValueAtTime(0, start);
      gain.gain.linearRampToValueAtTime(0.6, start + 0.05);
      gain.gain.linearRampToValueAtTime(0, start + duration);
      
      osc.connect(gain);
      gain.connect(audioCtx!.destination);
      
      osc.start(start);
      osc.stop(start + duration);
    };

    // Double beep: High then Low
    playBeep(880, now, 0.15); // A5
    playBeep(440, now + 0.2, 0.2); // A4
    
  } catch (e) {
    console.error("Audio playback failed", e);
  }
};
