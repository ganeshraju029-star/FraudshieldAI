import React, { useState } from 'react';
import { Dashboard } from '../components/Dashboard';
import { TransactionFeed } from '../components/TransactionFeed';
import { UserAnalytics } from '../components/UserAnalytics';
import { AdminPanel as AdminSettings } from '../components/AdminPanel';
import { Activity, ShieldAlert, Users, Settings, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';
import { useStore } from '../store';

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { transactionLimit, setTransactionLimit, userCurrency, simulationActive, toggleSimulation } = useStore();

  const navItems = [
    { id: 'dashboard', label: 'Metrics', icon: Activity },
    { id: 'monitor', label: 'Live Feed', icon: ShieldAlert },
    { id: 'analytics', label: 'Analysis', icon: Users },
    { id: 'admin', label: 'Simulation', icon: Settings },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard': return <Dashboard />;
      case 'monitor': return <TransactionFeed />;
      case 'analytics': return <UserAnalytics />;
      case 'admin': return (
        <div className="space-y-6">
          <div className="glass-panel p-6">
            <button onClick={toggleSimulation} className={`w-full py-2 rounded-lg font-medium transition-colors ${simulationActive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' : 'bg-slate-700 text-slate-400'}`}>
              {simulationActive ? 'Simulation Active' : 'Simulation Paused'}
            </button>
          </div>

          <div className="glass-panel p-6">
            <div className="flex items-center space-x-3 mb-6">
              <ShieldCheck className="text-blue-400" />
              <h3 className="text-lg font-semibold text-white">Security Policies</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">Global Transaction Limit</label>
                <div className="flex space-x-2">
                   <input 
                    type="number" 
                    value={transactionLimit}
                    onChange={(e) => setTransactionLimit(Number(e.target.value))}
                    className="flex-1 bg-navy-900 border border-white/10 rounded-lg px-3 py-2 text-white outline-none focus:border-blue-500"
                   />
                   <div className="bg-navy-900 border border-white/10 rounded-lg px-3 py-2 text-slate-400 text-sm flex items-center">
                     {userCurrency}
                   </div>
                </div>
                <p className="text-[10px] text-slate-500 mt-2">Transactions exceeding this value will be automatically blocked and flagged for review.</p>
              </div>
            </div>
          </div>
          <AdminSettings />
        </div>
      );
      default: return <Dashboard />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col p-6 max-w-[1600px] mx-auto w-full gap-6">
      <div className="flex items-center space-x-2 mb-2 border-b border-white/5 pb-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={clsx(
                "flex items-center space-x-2 px-4 py-2 rounded-lg transition-all text-sm font-medium",
                isActive 
                  ? "bg-white text-navy-900 border border-white" 
                  : "text-slate-400 hover:text-white hover:bg-white/5"
              )}
            >
              <Icon size={16} />
              <span>{item.label}</span>
            </button>
          )
        })}
      </div>
      
      <div className="w-full">
         {renderContent()}
      </div>
    </div>
  );
}
