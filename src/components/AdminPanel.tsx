import React, { useMemo, useState, useEffect } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { useStore } from '../store';
import { Settings, Play, Pause, Volume2, VolumeX, SlidersHorizontal, Trash2, Activity, ShieldAlert, CreditCard, Target, Shield, Lock, AlertTriangle, ActivitySquare } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell } from 'recharts';
import { generateMockTransaction, initAudio, playAlertSound } from '../utils/mockDataGenerator';
import { formatCurrency } from '../utils/formatCurrency';

export function AdminPanel() {
  const { 
    simulationActive, 
    toggleSimulation, 
    soundEnabled, 
    toggleSound, 
    fraudSensitivity, 
    setFraudSensitivity,
    addTransaction,
    setAlertTransaction,
    transactions,
    userCurrency
  } = useStore();

  const auditLog = useMemo(() => {
    return transactions.filter(t => t.payment_status || t.razorpay_order_id);
  }, [transactions]);

  const [activeTab, setActiveTab] = useState<'analytics' | 'graph'>('analytics');
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [xaiModal, setXaiModal] = useState({ show: false, txId: '', explanation: '', loading: false });
  const [isChaosActive, setIsChaosActive] = useState(false);
  const [lastGraphFetch, setLastGraphFetch] = useState(0);

  useEffect(() => {
    if (activeTab === 'graph') {
      const now = Date.now();
      if (now - lastGraphFetch > 3000 || graphData.nodes.length === 0) {
        fetch('/api/analytics/graph')
          .then(res => res.json())
          .then(data => {
            if (data && data.nodes) {
              setGraphData(data);
              setLastGraphFetch(now);
            }
          })
          .catch(console.error);
      }
    }
  }, [activeTab, transactions.length]);

  const handleChaosMode = async () => {
    if (isChaosActive) {
      setIsChaosActive(false);
      try {
        await fetch('/api/admin/chaos-mode/stop', { method: 'POST' });
      } catch(e) {}
    } else {
      setIsChaosActive(true);
      
      // Attempt backend call
      try {
        await fetch('/api/admin/chaos-mode', { method: 'POST' });
        // Even if successful, we set the active state
        setTimeout(() => setIsChaosActive(false), 3000);
      } catch(e) {
        // Fallback: Client-side burst injection
        console.debug("[Demo] Chaos Mode: Running client-side burst injection");
        
        let count = 0;
        const burstInterval = setInterval(() => {
           if (count >= 5) {
             clearInterval(burstInterval);
             setIsChaosActive(false);
             return;
           }
           
           const tx = generateMockTransaction(true); // Force high risk
           tx.riskScore = Math.floor(Math.random() * 10) + 90; // Overly risky for chaos!
           addTransaction(tx);
           
           // Trigger alert for the first and third injection for max visibility
           if (count === 0 || count === 2) {
             setAlertTransaction(tx);
           }
           
           count++;
        }, 300);
      }
    }
  };

  const handleExplain = async (txId: string) => {
    setXaiModal({ show: true, txId, explanation: '', loading: true });
    try {
      const res = await fetch(`/api/xai/explain/${txId}`);
      if(res.ok) {
        const data = await res.json();
        setXaiModal({ show: true, txId, explanation: data.explanation, loading: false });
      } else {
         setXaiModal({ show: true, txId, explanation: 'Failed to fetch explanation.', loading: false });
      }
    } catch(e) {}
  };

  const analytics = useMemo(() => {
    let totalProtectedVolume = 0;
    let capitalDefended = 0;
    let fraudCount = 0;
    let safeCount = 0;
    
    const scatterData = transactions.slice(0, 100).map(t => ({
      amount: t.amount,
      riskScore: t.riskScore,
      isFraud: t.isFraud,
      id: t.id
    }));

    transactions.forEach(t => {
      if (t.isFraud) {
        capitalDefended += t.amount;
        fraudCount++;
      } else {
        totalProtectedVolume += t.amount;
        safeCount++;
      }
    });

    const defconRatio = safeCount > 0 ? (fraudCount / (fraudCount + safeCount)) * 100 : 0;
    let defconLevel = 5;
    if (defconRatio > 30) defconLevel = 1;
    else if (defconRatio > 20) defconLevel = 2;
    else if (defconRatio > 10) defconLevel = 3;
    else if (defconRatio > 5) defconLevel = 4;

    return { totalProtectedVolume, capitalDefended, defconLevel, scatterData };
  }, [transactions]);

  const radarData = useMemo(() => [
    { subject: 'Velocity', A: Math.min(100, fraudSensitivity * 10 + 20), fullMark: 100 },
    { subject: 'Volume', A: Math.min(100, fraudSensitivity * 12 + 10), fullMark: 100 },
    { subject: 'Geospatial', A: Math.min(100, fraudSensitivity * 8 + 30), fullMark: 100 },
    { subject: 'Identity', A: Math.min(100, fraudSensitivity * 15), fullMark: 100 },
    { subject: 'Payload', A: Math.min(100, fraudSensitivity * 9 + 15), fullMark: 100 },
  ], [fraudSensitivity]);

  const handleForceFraud = () => {
    const tx = generateMockTransaction(true);
    addTransaction(tx);
    setAlertTransaction(tx);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="glass-panel p-8 rounded-2xl">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <Settings className="mr-2 text-slate-400" />
          Simulation Controls
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative">
          
          {/* Controls */}
          <div className="space-y-6">
            
            {/* Chaos Mode */}
            <div className="flex flex-col mb-4 p-4 bg-red-900/20 rounded-xl border border-red-500/30">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-white font-medium flex items-center">🔥 Launch Chaos Mode</h4>
                  <p className="text-sm text-slate-400">Inject 5 high-risk transactions</p>
                </div>
                <button 
                  onClick={handleChaosMode}
                  className={`px-4 py-2 ${isChaosActive ? 'bg-slate-700 hover:bg-slate-600 text-slate-300' : 'bg-red-600 hover:bg-red-500 text-white'} text-sm font-bold rounded-lg transition-colors shadow-[0_0_15px_rgba(220,38,38,0.5)]`}
                >
                  {isChaosActive ? 'STOP SIMULATION' : 'SIMULATE'}
                </button>
              </div>
            </div>

            {/* Toggle Engine */}
            <div className="flex items-center justify-between p-4 bg-navy-800 rounded-xl border border-white/5">
              <div>
                <h4 className="text-white font-medium">Data Stream Engine</h4>
                <p className="text-sm text-slate-400">Real-time mock transaction generation</p>
              </div>
              <button 
                onClick={toggleSimulation}
                className={`p-3 rounded-xl flex items-center justify-center transition-colors ${
                  simulationActive ? 'bg-alert-red hover:bg-red-600 text-white' : 'bg-alert-green hover:bg-green-600 text-navy-900'
                }`}
              >
                {simulationActive ? <Pause size={20} /> : <Play size={20} />}
              </button>
            </div>

            {/* Toggle Sound */}
            <div className="flex items-center justify-between p-4 bg-navy-800 rounded-xl border border-white/5">
              <div>
                <h4 className="text-white font-medium">Audio Alerts</h4>
                <p className="text-sm text-slate-400">Play beep on critical fraud</p>
              </div>
              <button 
                onClick={() => {
                  initAudio();
                  toggleSound();
                }}
                className={`p-3 rounded-xl flex items-center justify-center transition-colors ${
                  soundEnabled ? 'bg-neon-blue/20 text-neon-blue' : 'bg-white/5 text-slate-400'
                }`}
              >
                {soundEnabled ? <Volume2 size={20} /> : <VolumeX size={20} />}
              </button>
            </div>

            <div className="flex items-center justify-between p-4 bg-navy-800 rounded-xl border border-white/5">
              <div>
                <h4 className="text-white font-medium">Diagnostic</h4>
                <p className="text-sm text-slate-400">Hear the current alert sound</p>
              </div>
              <button 
                onClick={() => {
                  initAudio();
                  playAlertSound();
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium rounded-lg transition-colors border border-white/10"
              >
                Test Sound
              </button>
            </div>

             {/* Manual Injection */}
             <div className="flex items-center justify-between p-4 bg-navy-800 rounded-xl border border-white/5">
              <div>
                <h4 className="text-white font-medium">Force Injection</h4>
                <p className="text-sm text-slate-400">Manually trigger a critical alert</p>
              </div>
              <button 
                onClick={handleForceFraud}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium rounded-lg transition-colors shadow-[0_0_15px_rgba(147,51,234,0.3)]"
              >
                Inject Fraud
              </button>
            </div>

          </div>

          {/* Model Params */}
          <div className="space-y-6">
            
            <div className="p-6 bg-navy-800 rounded-xl border border-white/5">
              <h4 className="text-white font-medium flex items-center mb-4">
                <SlidersHorizontal size={18} className="mr-2 text-neon-blue" />
                AI Model Parameters
              </h4>
              
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-2">
                    <label className="text-sm text-slate-400">Detection Sensitivity (Mock)</label>
                    <span className="text-sm font-medium text-white">{fraudSensitivity}/10</span>
                  </div>
                  <input 
                    type="range" 
                    min="1" 
                    max="10" 
                    value={fraudSensitivity}
                    onChange={(e) => setFraudSensitivity(parseInt(e.target.value))}
                    className="w-full h-2 bg-navy-900 rounded-lg appearance-none cursor-pointer accent-neon-blue"
                  />
                  <div className="flex justify-between mt-1 text-xs text-slate-500">
                    <span>Conservative</span>
                    <span>Aggressive</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5">
                  <p className="text-xs text-slate-400 italic">
                    Increasing sensitivity forces the simulation engine to generate more fraudulent transactions, simulating a targeted attack on the network.
                  </p>
                </div>
              </div>
            </div>

          </div>
        </div>
      </div>

      {/* Deep Threat Analytics */}
      <div className="glass-panel p-8 rounded-2xl border border-white/10 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2"></div>
        {/* Title and Tabs */}
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-xl font-bold text-white flex items-center">
            <ActivitySquare className="mr-3 text-purple-400" />
            Deep Threat Analytics
          </h2>
          <div className="flex space-x-2 bg-navy-900 rounded-lg p-1 border border-white/10">
            <button 
              onClick={() => setActiveTab('analytics')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'analytics' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Metrics
            </button>
            <button 
              onClick={() => setActiveTab('graph')}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeTab === 'graph' ? 'bg-purple-600 text-white' : 'text-slate-400 hover:text-white'}`}
            >
              Graph Topology
            </button>
          </div>
        </div>

        {activeTab === 'analytics' ? (
          <>
        {/* Telemetry Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
          <div className="bg-[#0e2136] p-6 rounded-xl border border-white/5 border-l-4 border-l-blue-500 relative">
            <Shield className="absolute top-4 right-4 text-blue-500/20" size={48} />
            <p className="text-sm font-medium text-slate-400 mb-1">Total Protected Volume</p>
            <p className="text-3xl font-bold text-white">{formatCurrency(analytics.totalProtectedVolume, userCurrency)}</p>
          </div>
          <div className="bg-[#0e2136] p-6 rounded-xl border border-white/5 border-l-4 border-l-emerald-500 relative">
            <Lock className="absolute top-4 right-4 text-emerald-500/20" size={48} />
            <p className="text-sm font-medium text-slate-400 mb-1">Capital Defended</p>
            <p className="text-3xl font-bold text-emerald-400">{formatCurrency(analytics.capitalDefended, userCurrency)}</p>
          </div>
          <div className="bg-[#0e2136] p-6 rounded-xl border border-white/5 border-l-4 border-l-red-500 relative overflow-hidden">
            <AlertTriangle className="absolute top-4 right-4 text-red-500/20" size={48} />
            <p className="text-sm font-medium text-slate-400 mb-1">Threat Defcon Level</p>
            <div className="flex items-baseline space-x-2">
              <p className="text-3xl font-bold text-red-400">DEFCON {analytics.defconLevel}</p>
            </div>
            {analytics.defconLevel <= 2 && <div className="absolute bottom-0 left-0 w-full h-1 bg-red-500 animate-pulse"></div>}
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Radar Chart */}
          <div className="bg-[#0e2136] p-6 rounded-xl border border-white/5">
             <h3 className="text-sm font-semibold text-white mb-6 uppercase tracking-widest flex items-center">
               <Target size={16} className="mr-2 text-purple-400" /> AI Vector Radar
             </h3>
             <div className="h-64 w-full flex items-center justify-center">
               <ResponsiveContainer width="100%" height="100%">
                 <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                   <PolarGrid stroke="#334155" />
                   <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                   <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#475569' }} />
                   <Radar name="Active Weights" dataKey="A" stroke="#a855f7" strokeWidth={2} fill="#a855f7" fillOpacity={0.3} isAnimationActive={false} />
                   <RechartsTooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} itemStyle={{ color: '#a855f7' }} />
                 </RadarChart>
               </ResponsiveContainer>
             </div>
          </div>

          {/* Scatter Chart */}
          <div className="bg-[#0e2136] p-6 rounded-xl border border-white/5">
             <h3 className="text-sm font-semibold text-white mb-6 uppercase tracking-widest">Algorithmic Clustering</h3>
             <div className="h-64 w-full">
               <ResponsiveContainer width="100%" height="100%">
                 <ScatterChart margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
                   <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                   <XAxis type="number" dataKey="amount" name="Amount" tick={{ fill: '#64748b' }} axisLine={{ stroke: '#334155' }} tickLine={false} />
                   <YAxis type="number" dataKey="riskScore" name="Risk Score" tick={{ fill: '#64748b' }} axisLine={{ stroke: '#334155' }} tickLine={false} domain={[0, 100]} />
                   <RechartsTooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b' }} labelStyle={{ color: '#fff' }} />
                   <Scatter name="Transactions" data={analytics.scatterData} fill="#3b82f6" isAnimationActive={false}>
                     {analytics.scatterData.map((entry, index) => (
                       <Cell key={`cell-${index}`} fill={entry.isFraud ? '#ef4444' : '#3b82f6'} />
                     ))}
                   </Scatter>
                 </ScatterChart>
               </ResponsiveContainer>
             </div>
          </div>

        </div>
          </>
        ) : (
          <div className="bg-[#0e2136] rounded-xl border border-white/5 overflow-hidden" style={{ height: '600px' }}>
            <h3 className="text-sm font-semibold text-white p-4 uppercase tracking-widest border-b border-white/5">Investigation Graph</h3>
            {graphData.nodes.length > 0 ? (
              <MemoizedGraph data={graphData} />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-500">Processing transactional graph topology...</div>
            )}
          </div>
        )}
      </div>

      {/* XAI Modal */}
      {xaiModal.show && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-[#0e2136] border border-purple-500/30 rounded-2xl shadow-2xl p-6 max-w-lg w-full">
            <h3 className="text-xl font-bold text-white mb-4 flex items-center">
              <SlidersHorizontal className="mr-2 text-purple-400" />
              Explainable AI (XAI)
            </h3>
            <p className="text-sm text-slate-400 mb-6">Deep reasoning insight for Transaction: <span className="font-mono text-purple-300">{xaiModal.txId}</span></p>
            <div className="bg-navy-900 p-4 rounded-xl border border-white/5 text-slate-300 min-h-[100px] text-sm leading-relaxed whitespace-pre-wrap">
              {xaiModal.loading ? (
                <div className="animate-pulse flex items-center text-purple-400">
                  <div className="w-4 h-4 rounded-full border-2 border-purple-500 border-t-transparent animate-spin mr-3"></div>
                  Generating logic flow...
                </div>
              ) : (
                xaiModal.explanation
              )}
            </div>
            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setXaiModal({ ...xaiModal, show: false })}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Gateway Audit Trail */}
      <div className="glass-panel p-8 rounded-2xl">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <Activity className="mr-2 text-neon-blue" />
          Gateway Audit Trail
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs text-slate-400 uppercase bg-navy-900/50 border-b border-white/5">
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">Order ID</th>
                <th className="px-4 py-3">Gateway Status</th>
                <th className="px-4 py-3">Risk Score</th>
                <th className="px-4 py-3">Amount</th>
                <th className="px-4 py-3">Target Account</th>
                <th className="px-4 py-3 rounded-tr-lg">Action</th>
              </tr>
            </thead>
            <tbody>
              {auditLog.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">No Gateway transactions logged in current session.</td>
                </tr>
              ) : (
                auditLog.map((tx, idx) => (
                  <tr key={idx} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 font-mono text-xs">{tx.razorpay_order_id || tx.id}</td>
                    <td className="px-4 py-3">
                       {tx.payment_status === 'verified' && <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded-md text-xs border border-blue-500/30">Verified</span>}
                       {tx.status === 'refunded' && <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 rounded-md text-xs border border-yellow-500/30">Refunded</span>}
                       {tx.payment_status === 'blocked_by_fraud_detection' && <span className="px-2 py-1 bg-alert-red/20 text-alert-red rounded-md text-xs border border-alert-red/30">Blocked</span>}
                       {(!tx.payment_status || tx.payment_status === 'pending') && tx.status !== 'refunded' && <span className="px-2 py-1 bg-slate-500/20 text-slate-400 rounded-md text-xs border border-slate-500/30">Pending</span>}
                    </td>
                    <td className="px-4 py-3">
                       <span className={`font-semibold ${tx.riskScore > 80 ? 'text-alert-red' : 'text-alert-green'}`}>{tx.riskScore}/100</span>
                    </td>
                    <td className="px-4 py-3 font-medium text-white">{formatCurrency(tx.amount, userCurrency)}</td>
                    <td className="px-4 py-3 truncate max-w-[150px]">{tx.target_account || 'N/A'}</td>
                    <td className="px-4 py-3">
                      {(tx.riskScore > 50 || tx.isFraud) && (
                        <button onClick={() => handleExplain(tx.id || tx.razorpay_order_id || '')} className="px-3 py-1 bg-purple-600/20 text-purple-400 border border-purple-500/30 rounded hover:bg-purple-600/40 transition-colors text-xs whitespace-nowrap">
                          Explain
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

const MemoizedGraph = React.memo(({ data }: { data: any }) => {
  return (
    <ForceGraph2D
      graphData={data}
      nodeAutoColorBy="group"
      nodeRelSize={6}
      linkColor={() => '#475569'}
      backgroundColor="#0e2136"
      nodeLabel="name"
      d3AlphaDecay={0.05} // Faster stabilization
      cooldownTicks={50} // Stop simulation after 50 ticks to save CPU
      nodeCanvasObject={(node: any, ctx: any, globalScale: number) => {
        const label = node.name;
        const fontSize = 12/globalScale;
        ctx.font = `${fontSize}px Sans-Serif`;
        const textWidth = ctx.measureText(label).width;
        const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

        ctx.fillStyle = 'rgba(14, 33, 54, 0.8)';
        ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y - bckgDimensions[1] / 2, bckgDimensions[0], bckgDimensions[1]);

        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = node.color;
        ctx.fillText(label, node.x, node.y);

        node.__bckgDimensions = bckgDimensions;
      }}
    />
  );
}, (prev, next) => {
  // Only re-render if nodes or links count change
  return prev.data.nodes.length === next.data.nodes.length && prev.data.links.length === next.data.links.length;
});
