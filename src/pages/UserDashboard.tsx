import React, { useState, useRef } from 'react';
import { useStore } from '../store';
import { CreditCard, Activity, ShieldCheck, DollarSign, Send, Zap, RefreshCcw, CheckCircle2, XCircle, QrCode, UploadCloud, X } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import jsQR from 'jsqr';
import { generateMockTransaction, evaluateFraudRisk, LOCATIONS, CATEGORIES, initAudio, playAlertSound } from '../utils/mockDataGenerator';
import { formatCurrency } from '../utils/formatCurrency';

export function UserDashboard() {
  const { currentUser, users, setPin, transactions, addTransaction, setAlertTransaction, soundEnabled, userLocation, userCurrency, userBalance, adjustBalance, connectBank } = useStore();
  
  const [payAmount, setPayAmount] = useState('');
  const [payCategory, setPayCategory] = useState(CATEGORIES[0]);
  const [payLocation, setPayLocation] = useState(LOCATIONS[0].name);
  const [payTarget, setPayTarget] = useState('');

  const [paymentStatus, setPaymentStatus] = useState<{show: boolean, type: 'success'|'error', msg: string} | null>(null);

  const [isUnlocked, setIsUnlocked] = useState(false);
  const [pinInput, setPinInput] = useState('');
  const [newPinInput, setNewPinInput] = useState('');

  // Bank Info form
  const [bankName, setBankName] = useState('');
  const [accNumber, setAccNumber] = useState('');
  const [isConnecting, setIsConnecting] = useState(false);

  // QR Scanner Modal
  const [showQRScanner, setShowQRScanner] = useState(false);
  const [scanError, setScanError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setScanError('');
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        canvas.width = img.width;
        canvas.height = img.height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(img, 0, 0, img.width, img.height);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          if (code) {
             try {
               const data = JSON.parse(code.data);
               if (data.target_account) setPayTarget(data.target_account);
               if (data.amount) setPayAmount(data.amount.toString());
               if (data.category) setPayCategory(data.category);
               if (data.location) setPayLocation(data.location);
               setShowQRScanner(false);
               initAudio();
               setPaymentStatus({ show: true, type: 'success', msg: 'QR Code scanned successfully! Details auto-filled.' });
               setTimeout(() => setPaymentStatus(null), 3000);
             } catch(err) {
               setScanError('QR format unrecognized. Not a valid JSON payload.');
             }
          } else {
             setScanError('No readable QR code found in the image.');
          }
        }
      };
      img.src = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  };
  // Behavioral Biometrics
  const [keystrokes, setKeystrokes] = useState<number[]>([]);
  const [mouseMoves, setMouseMoves] = useState<{x: number, y: number}[]>([]);

  const handleKeyDown = () => {
    setKeystrokes(prev => [...prev.slice(-10), Date.now()]);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (Math.random() < 0.2) {
       setMouseMoves(prev => [...prev.slice(-20), {x: e.clientX, y: e.clientY}]);
    }
  };

  const getBiometrics = () => {
     let typingSpeedMs = 150 + Math.random() * 50; // default human speed
     if (keystrokes.length > 2) {
       const diffs = [];
       for(let i=1; i<keystrokes.length; i++) diffs.push(keystrokes[i] - keystrokes[i-1]);
       typingSpeedMs = diffs.reduce((a,b)=>a+b, 0) / diffs.length;
     }
     
     let mouseJitter = 5 + Math.random() * 5; // default human jitter
     if (mouseMoves.length > 2) {
       let jitterSum = 0;
       for(let i=1; i<mouseMoves.length; i++) {
          jitterSum += Math.abs(mouseMoves[i].y - mouseMoves[i-1].y);
       }
       mouseJitter = jitterSum / mouseMoves.length;
     }

     return { typingSpeedMs, mouseJitter };
  };

  const userTransactions = transactions.filter(t => t.userId === currentUser?.id).slice(0, 5);

  const spendData = [
    { date: 'Mon', amount: 120 },
    { date: 'Tue', amount: 45 },
    { date: 'Wed', amount: 350 },
    { date: 'Thu', amount: 15 },
    { date: 'Fri', amount: 90 },
    { date: 'Sat', amount: 210 },
    { date: 'Sun', amount: 55 },
  ];

  const handlePayment = async (e: React.FormEvent) => {
    initAudio();
    e.preventDefault();
    if (!isUnlocked) return;
    
    const amountNum = parseFloat(payAmount);
    if (!amountNum || amountNum <= 0) return;

    const bio = getBiometrics();
    let payload;

    try {
      try {
        const res = await fetch('/api/payment/create-order', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            user_id: currentUser?.id || 'usr_demo',
            amount: amountNum,
            location: payLocation,
            category: payCategory,
            target_account: payTarget,
            device_id: 'web_dashboard',
            biometrics: bio
          })
        });
        
        payload = await res.json();
        
        if (!res.ok) {
           if (res.status === 403 && payload.detail?.error) {
              setPaymentStatus({ show: true, type: 'error', msg: `Transaction blocked by FraudShield. Reason: ${payload.detail.flag_reason}` });
              setAlertTransaction({
                 id: `tx_blocked_${Math.random().toString(36).substring(2,8)}`,
                 userId: currentUser?.id || 'usr_demo',
                 amount: amountNum,
                 location: payLocation,
                 category: payCategory,
                 riskScore: payload.detail.risk_score,
                 isFraud: true,
                 status: 'fraud',
                 flagReason: payload.detail.flag_reason,
                 lat: 0, lng: 0,
                 timestamp: Date.now()
              });
           } else {
              setPaymentStatus({ show: true, type: 'error', msg: payload.detail?.error || 'Failed to initialize payment.' });
           }
           return;
        }
      } catch (err) {
        console.warn("Backend API unavailable, using mock order generation for demo site.");
        // Mock order payload for Netlify demo
        payload = {
            order: {
                id: `order_mock_${Math.random().toString(36).substring(2,9)}`,
                order_id: `rzp_test_${Math.random().toString(36).substring(2,9)}`,
                risk_score: 15 + Math.random() * 20
            }
        };
      }
      
      const order = payload.order;

      if (amountNum > userBalance) {
        setPaymentStatus({ show: true, type: 'error', msg: 'Insufficient Funds.' });
      } else {
        try {
          const options = {
            key: 'rzp_test_1DP5mmOlF5G5ag',
            amount: amountNum * 100,
            currency: 'INR',
            name: 'FraudShield Sandbox',
            description: 'Express Transfer',
            order_id: order.order_id || order.id,
            handler: async function (response: any) {
              // Verify on the backend
              const vRes = await fetch('/api/payment/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature || 'mock_signature'
                })
              });
              if (vRes.ok) {
                 adjustBalance(-amountNum); 
                 
                 addTransaction({
                   id: response.razorpay_payment_id || `tx_${Math.random().toString(36).substring(2,8)}`,
                   userId: currentUser?.id || 'usr_demo',
                   amount: amountNum,
                   location: payLocation,
                   category: payCategory,
                   riskScore: order.risk_score || 0,
                   isFraud: false,
                   status: 'safe',
                   target_account: payTarget,
                   payment_id: response.razorpay_payment_id,
                   payment_status: 'verified',
                   lat: 0,
                   lng: 0,
                   timestamp: Date.now()
                 });

                 setPaymentStatus({ show: true, type: 'success', msg: `Transfer of ${formatCurrency(amountNum, userCurrency)} via Razorpay completed Successfully.` });
                 setPayAmount('');
                 setPayTarget('');
              } else {
                 // Mock success for Netlify if verification fails
                 if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
                    adjustBalance(-amountNum);
                    addTransaction({
                        id: response.razorpay_payment_id || `tx_mock_${Math.random().toString(36).substring(2,8)}`,
                        userId: currentUser?.id || 'usr_demo',
                        amount: amountNum,
                        location: payLocation,
                        category: payCategory,
                        riskScore: order.risk_score || 0,
                        isFraud: false,
                        status: 'safe',
                        target_account: payTarget,
                        payment_id: response.razorpay_payment_id,
                        payment_status: 'verified',
                        lat: 0, lng: 0,
                        timestamp: Date.now()
                    });
                    setPaymentStatus({ show: true, type: 'success', msg: `Transfer of ${formatCurrency(amountNum, userCurrency)} completed successfully (Demo Mode).` });
                    setPayAmount('');
                    setPayTarget('');
                 } else {
                    setPaymentStatus({ show: true, type: 'error', msg: `Payment verification failed at backend.` });
                 }
              }
            },
            prefill: {
              name: currentUser?.name || 'Authorized User'
            },
            theme: { color: '#3b82f6' }
          };

          if (!(window as any).Razorpay) {
            setPaymentStatus({ show: true, type: 'error', msg: 'Razorpay SDK is loading. Try again.' });
            return;
          }

          const rzp = new (window as any).Razorpay(options);
          rzp.on('payment.failed', function (response: any) {
            setPaymentStatus({ show: true, type: 'error', msg: `Razorpay Error: ${response.error.description}` });
          });
          rzp.open();
        } catch (rzpErr) {
          console.error("Razorpay Error:", rzpErr);
          setPaymentStatus({ show: true, type: 'error', msg: 'Payment Gateway initialization failed.' });
        }
      }
    } catch (err) {
      console.error("Payment failed", err);
      setPaymentStatus({ show: true, type: 'error', msg: 'Transaction failed to process.' });
    }
  };

  const handleRefund = async (paymentId: string | undefined) => {
    if(!paymentId) return;
    try {
      const res = await fetch('/api/payment/refund', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({ payment_id: paymentId, reason: "Customer requested dashboard refund" })
      });
      if (res.ok) {
         setPaymentStatus({ show: true, type: 'success', msg: `Refund requested successfully!` });
      } else {
         setPaymentStatus({ show: true, type: 'error', msg: `Failed to process refund. Check gateway.` });
      }
      setTimeout(() => setPaymentStatus(null), 3000);
    } catch(e) {
      console.error(e);
    }

    setPayAmount('');
    setTimeout(() => setPaymentStatus(null), 5000);
  };

  const expectedPin = (currentUser && users?.[currentUser.name]?.pin) || '1234';

  const handleUnlock = (e: React.FormEvent) => {
    initAudio();
    e.preventDefault();
    if (pinInput === expectedPin) {
      setIsUnlocked(true);
      setPinInput('');
    } else {
      setPaymentStatus({ show: true, type: 'error', msg: 'Invalid PIN. Please try again.' });
      setTimeout(() => setPaymentStatus(null), 3000);
    }
  };

  const handleChangePin = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPinInput.length !== 4) {
       setPaymentStatus({ show: true, type: 'error', msg: 'PIN must be exactly 4 digits.' });
       setTimeout(() => setPaymentStatus(null), 3000);
       return;
    }
    setPin(newPinInput);
    setNewPinInput('');
    setPaymentStatus({ show: true, type: 'success', msg: 'Security PIN has been updated.' });
    setTimeout(() => setPaymentStatus(null), 3000);
  };

  const handleAddFunds = () => {
    if (!isUnlocked) return;
    adjustBalance(1000);
    setPaymentStatus({ show: true, type: 'success', msg: '+$1,000.00 added to Top-up.' });
    setTimeout(() => setPaymentStatus(null), 3000);
  };

  const handleBankConnect = (e: React.FormEvent) => {
    initAudio();
    e.preventDefault();
    if (!bankName || !accNumber) return;
    setIsConnecting(true);

    setTimeout(() => {
       // Set initial balance
       const startingBalance = Math.floor(Math.random() * 25000) + 2000;
       connectBank(startingBalance);
       setIsConnecting(false);

       // Generate historical transactions
       for (let i = 0; i < 8; i++) {
         const newT = generateMockTransaction();
         newT.id = `tx_hist_${Math.random().toString(36).substring(2,8)}`;
         newT.userId = currentUser!.id;
         // Adjust risk slightly so it's mostly safe
         newT.isFraud = false;
         newT.status = 'safe';
         addTransaction(newT);
       }
    }, 2500);
  };

  if (currentUser && !currentUser.bankConnected) {
    return (
      <div className="flex items-center justify-center min-h-[80vh] p-4">
        <div className="bg-navy-800 border border-white/10 p-8 rounded-2xl shadow-2xl max-w-md w-full relative overflow-hidden">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl"></div>
          
          <div className="flex justify-center mb-6">
             <div className="w-16 h-16 bg-navy-900 border border-white/10 rounded-2xl flex items-center justify-center shadow-lg">
                <ShieldCheck size={32} className="text-blue-400" />
             </div>
          </div>
          <h2 className="text-2xl font-bold text-white text-center mb-2">Connect Institution</h2>
          <p className="text-sm text-slate-400 text-center mb-8">Link your bank account ledger. FraudShield AI will instantly analyze your history for anomalies.</p>
          
          {isConnecting ? (
             <div className="flex flex-col items-center py-6">
                <div className="w-10 h-10 border-4 border-slate-700 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                <p className="text-blue-400 font-medium animate-pulse">Syncing Ledger Details...</p>
             </div>
          ) : (
            <form onSubmit={handleBankConnect} className="space-y-4 relative z-10">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Institution Name</label>
                <input 
                  type="text" 
                  value={bankName}
                  onChange={(e) => setBankName(e.target.value)}
                  placeholder="e.g. Chase, Bank of America" 
                  autoFocus
                  required
                  className="w-full bg-navy-900 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Account / Routing Number</label>
                <input 
                  type="password" 
                  value={accNumber}
                  onChange={(e) => setAccNumber(e.target.value)}
                  placeholder="•••• •••• ••••" 
                  required
                  className="w-full bg-navy-900 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 tracking-widest"
                />
              </div>
              <button type="submit" className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-4 rounded-xl transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                Securely Connect
              </button>
            </form>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6">
      
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center bg-[#0e2136] rounded-2xl p-8 border border-white/5 shadow-md">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Welcome back, {currentUser?.name || 'User'}</h2>
          <p className="text-slate-400">
            {userLocation ? `Location locked to ${userLocation.city}, ${userLocation.country}. ` : 'Your account security status is active.'}
          </p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-full text-emerald-400 font-medium">
          <ShieldCheck size={18} className="mr-2" />
          Protected by FraudShield AI
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Creative Payment Form */}
          <div className="bg-gradient-to-br from-[#0e2136] to-[#122842] p-8 rounded-2xl border border-white/10 shadow-lg relative overflow-hidden">
            <div className="absolute -top-10 -right-10 w-40 h-40 bg-blue-500/10 rounded-full blur-3xl"></div>
            
            <h3 className="text-lg font-semibold text-white mb-2 flex items-center">
               <Zap className="mr-2 text-blue-400" size={20} />
               Express Payment
            </h3>
            <p className="text-sm text-slate-400 mb-6">Send funds globally. All transactions are monitored in real-time by FraudShield AI.</p>
            
            <form onSubmit={handlePayment} onMouseMove={handleMouseMove} onKeyDown={handleKeyDown} className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-300 mb-2">Destination Account / UPI ID</label>
                <div className="relative flex items-center">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Activity size={18} className="text-slate-400" />
                  </div>
                  <input
                    type="text"
                    value={payTarget}
                    onChange={(e) => setPayTarget(e.target.value)}
                    className="w-full bg-navy-900 border border-slate-700/50 rounded-xl pl-10 pr-12 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    placeholder="user@okicici or Account Number"
                    required
                  />
                  <button 
                    type="button"
                    onClick={() => setShowQRScanner(true)}
                    className="absolute right-3 p-1.5 text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded-lg transition-colors cursor-pointer"
                    title="Scan QR Code"
                  >
                    <QrCode size={20} />
                  </button>
                </div>
              </div>
              
              <div className="md:col-span-2 mt-4">
                <label className="block text-sm font-medium text-slate-300 mb-2">Transfer Amount ({userCurrency})</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <DollarSign size={18} className="text-slate-400" />
                  </div>
                  <input
                    type="number"
                    value={payAmount}
                    onChange={(e) => setPayAmount(e.target.value)}
                    className="w-full bg-navy-900 border border-slate-700/50 rounded-xl pl-10 pr-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    placeholder="0.00"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Merchant Category</label>
                <select 
                  value={payCategory}
                  onChange={(e) => setPayCategory(e.target.value)}
                  className="w-full bg-navy-900 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
                >
                  {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Simulated IP Location</label>
                <select 
                  value={payLocation}
                  onChange={(e) => setPayLocation(e.target.value)}
                  className="w-full bg-navy-900 border border-slate-700/50 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 appearance-none"
                >
                  {LOCATIONS.map(l => <option key={l.name} value={l.name}>{l.name}</option>)}
                </select>
              </div>

              <div className="md:col-span-2 flex items-center justify-between mt-2">
                <div className="flex-1 mr-4">
                  {paymentStatus && (
                    <div className={`p-3 rounded-lg text-sm border ${
                      paymentStatus.type === 'success' 
                        ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                        : 'bg-red-500/10 border-red-500/30 text-red-400'
                    }`}>
                      {paymentStatus.msg}
                    </div>
                  )}
                </div>
                <button 
                  type="submit" 
                  disabled={!isUnlocked}
                  className={`font-medium py-3 px-8 rounded-xl transition-all flex items-center ${
                    isUnlocked 
                      ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-[0_0_15px_rgba(59,130,246,0.3)]' 
                      : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                  }`}
                >
                  Execute Transfer
                  <Send size={16} className="ml-2" />
                </button>
              </div>

              {/* Simulation Controls for Demo */}
              <div className="md:col-span-2 pt-4 mt-4 border-t border-white/5 flex items-center justify-between">
                <div className="text-xs text-slate-500 max-w-[250px]">
                  <strong>Demo Mode:</strong> Use this to verify the FraudShield AI alert popups are operational.
                </div>
                <button 
                  type="button" 
                  onClick={() => {
                     initAudio();
                     const testTx = generateMockTransaction(true); 
                     testTx.riskScore = 98;
                     setAlertTransaction(testTx);
                  }}
                  className="text-xs bg-alert-red/10 hover:bg-alert-red/20 text-alert-red px-4 py-2 rounded-lg border border-alert-red/20 transition-all font-semibold uppercase tracking-wider"
                >
                  Trigger Test Alert
                </button>
              </div>
            </form>
            
            {/* PIN Overlay for Payment */}
            {!isUnlocked && (
              <div className="absolute inset-0 z-20 bg-[#0e2136]/90 backdrop-blur-sm flex flex-col items-center justify-center rounded-2xl border border-white/5">
                <div className="bg-navy-900 border border-white/10 p-6 rounded-2xl shadow-2xl text-center max-w-sm">
                  <ShieldCheck size={32} className="mx-auto text-blue-400 mb-4" />
                  <h4 className="text-white font-semibold mb-2">Authentication Required</h4>
                  <p className="text-sm text-slate-400 mb-6">Enter your security PIN (1234) to unlock card functionality.</p>
                  
                  <form onSubmit={handleUnlock} className="flex space-x-2">
                    <input 
                      type="password" 
                      maxLength={4}
                      value={pinInput}
                      onChange={(e) => setPinInput(e.target.value.replace(/\D/g, ''))}
                      placeholder="PIN" 
                      className="w-full bg-[#0e2136] border border-white/10 rounded-lg px-4 py-2 text-white text-center tracking-widest outline-none focus:border-blue-500 transition-colors"
                    />
                    <button type="submit" className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg text-white font-medium transition-colors">
                      Verify
                    </button>
                  </form>
                </div>
              </div>
            )}

            {/* QR Scanner Modal */}
            {showQRScanner && (
              <div className="absolute inset-0 z-30 bg-[#0e2136]/90 backdrop-blur-md flex flex-col items-center justify-center rounded-2xl border border-white/10 shadow-2xl transition-all">
                <button 
                  type="button"
                  onClick={() => setShowQRScanner(false)}
                  className="absolute top-4 right-4 p-2 text-slate-400 hover:text-white bg-slate-800/50 hover:bg-slate-700 rounded-full transition-colors"
                >
                  <X size={20} />
                </button>
                
                <div className="bg-navy-900 border border-white/10 p-8 rounded-2xl shadow-[0_0_40px_rgba(59,130,246,0.15)] text-center max-w-sm w-full mx-4">
                  <div className="w-16 h-16 bg-blue-500/10 border border-blue-500/30 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                     <QrCode size={32} className="text-blue-400" />
                  </div>
                  
                  <h4 className="text-xl text-white font-semibold mb-2">Scan Payment QR</h4>
                  <p className="text-sm text-slate-400 mb-6">Upload an invoice QR code to automatically fill in the transaction details securely.</p>
                  
                  <div 
                    className="border-2 border-dashed border-slate-600 hover:border-blue-500/50 bg-slate-800/30 hover:bg-slate-800/50 transition-colors rounded-xl p-8 cursor-pointer relative group flex flex-col items-center justify-center"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <UploadCloud size={32} className="text-slate-400 group-hover:text-blue-400 mb-3 transition-colors" />
                    <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">Click to upload image</span>
                    <span className="text-xs text-slate-500 mt-1">Supports PNG, JPG</span>
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      className="hidden" 
                      accept="image/*"
                      onChange={handleFileUpload}
                    />
                  </div>
                  
                  {scanError && (
                     <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start text-left">
                       <XCircle size={16} className="text-red-400 mr-2 mt-0.5 flex-shrink-0" />
                       <span className="text-xs text-red-400">{scanError}</span>
                     </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Spending Chart */}
          <div className="bg-[#0e2136] p-6 rounded-2xl border border-white/5 shadow-md">
            <h3 className="text-lg font-semibold text-white mb-6">Weekly Spending Overview</h3>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={spendData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="date" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => formatCurrency(val, userCurrency).replace(/\.00$/, '')} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#112236', borderColor: '#1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Line type="monotone" dataKey="amount" stroke="#94a3b8" strokeWidth={3} dot={{ fill: '#0f172a', strokeWidth: 2 }} activeDot={{ r: 6, fill: '#fff' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>

        {/* Right Column / Cards */}
        <div className="space-y-8">
          <div className="bg-gradient-to-br from-slate-800 to-navy-900 p-6 rounded-2xl border border-white/10 shadow-lg relative overflow-hidden">
             <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2"></div>
             
             <div className="flex justify-between items-center mb-10">
               <CreditCard className="text-slate-300" size={24} />
               <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/2/2a/Mastercard-logo.svg/1280px-Mastercard-logo.svg.png" alt="Card Logo" className="w-10 opacity-80" />
             </div>
             <div className="space-y-1">
                <p className="text-slate-400 text-xs uppercase tracking-widest">Card Balance</p>
                <div className="flex items-center space-x-4">
                  <p className="text-3xl font-bold text-white">
                    {isUnlocked ? formatCurrency(userBalance, userCurrency) : '****'}
                  </p>
                  {isUnlocked && (
                    <button 
                      onClick={handleAddFunds}
                      className="text-xs bg-white/10 hover:bg-white/20 text-white px-2 py-1 rounded transition-colors"
                    >
                      + Top Up
                    </button>
                  )}
                </div>
             </div>
             <div className="mt-8 flex justify-between text-sm text-slate-300 font-mono">
               <span>**** **** **** 8892</span>
               <span>08/28</span>
             </div>
          </div>

          {isUnlocked && (
           <div className="bg-[#0e2136] rounded-2xl border border-white/5 p-6 shadow-md">
             <h3 className="text-sm font-semibold text-white mb-4">Security Preferences</h3>
             <form onSubmit={handleChangePin} className="flex space-x-2">
                <input 
                  type="password" 
                  maxLength={4}
                  value={newPinInput}
                  onChange={(e) => setNewPinInput(e.target.value.replace(/\D/g, ''))}
                  placeholder="New 4-Digit PIN" 
                  className="w-full bg-navy-900 border border-slate-700/50 rounded-lg px-4 py-2 text-white text-center tracking-widest outline-none focus:border-blue-500 transition-colors"
                />
                <button type="submit" className="bg-slate-700 hover:bg-slate-600 px-4 py-2 rounded-lg text-white font-medium transition-colors text-sm whitespace-nowrap">
                  Update PIN
                </button>
              </form>
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                <div className="text-xs text-slate-400">Audio verification diagnostic</div>
                <button 
                  onClick={() => {
                    initAudio();
                    playAlertSound();
                  }}
                  className="px-3 py-1 bg-white/5 hover:bg-white/10 text-slate-300 text-xs rounded border border-white/10 transition-colors"
                >
                  Sound Check
                </button>
              </div>
            </div>
          )}

           {/* Recent Transactions */}
           <div className="bg-[#0e2136] rounded-2xl border border-white/5 shadow-md overflow-hidden">
             <div className="p-6 border-b border-white/5 flex justify-between items-center">
               <h3 className="text-lg font-semibold text-white">Your Feed</h3>
             </div>
             <div className="divide-y divide-white/5">
                {userTransactions.length === 0 ? (
                  <div className="p-8 text-center text-slate-400 text-sm">
                    No recent transactions found.
                  </div>
                ) : (
                  userTransactions.map((tx, i) => (
                    <div key={i} className="p-4 px-6 flex justify-between items-center hover:bg-white/[0.02] transition-colors">
                      <div className="flex items-center space-x-4">
                        <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                          {tx.isFraud ? (
                            <XCircle size={18} className="text-alert-red" />
                          ) : (
                            <CheckCircle2 size={18} className="text-emerald-500" />
                          )}
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                             <p className="font-medium text-white">{tx.category}</p>
                             {tx.payment_status === 'verified' && <span className="text-[10px] px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">Paid</span>}
                             {tx.status === 'refunded' && <span className="text-[10px] px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded-full border border-yellow-500/30">Refunded</span>}
                             {tx.isFraud && <span className="text-[10px] px-2 py-0.5 bg-alert-red/20 text-alert-red rounded-full border border-alert-red/30">Blocked</span>}
                          </div>
                          <p className="text-xs text-slate-500 truncate max-w-[120px]">{tx.target_account || tx.location}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end">
                        <p className={`font-medium ${tx.isFraud ? 'text-alert-red' : 'text-white'}`}>
                          {formatCurrency(tx.amount, userCurrency)}
                        </p>
                        {tx.payment_status === 'verified' && tx.status !== 'refunded' && (
                           <button onClick={() => handleRefund(tx.payment_id)} className="flex items-center mt-1 text-[10px] text-slate-400 hover:text-white transition-colors">
                             <RefreshCcw size={10} className="mr-1" /> Refund
                           </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
             </div>
          </div>
        </div>

      </div>
    </div>
  );
}
