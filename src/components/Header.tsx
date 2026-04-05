import React from 'react';
import { useStore } from '../store';
import { LogOut, User, ShieldCheck, Bell } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function Header() {
  const { currentUser, logout, alertTransaction } = useStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-navy-900 border-b border-white/5 flex items-center justify-between px-6 z-20 shrink-0">
      <div className="flex items-center space-x-3">
        <img src="/logo.png" alt="FraudShield AI Logo" className="h-8 object-contain" onError={(e) => {
          e.currentTarget.style.display = 'none';
          if (e.currentTarget.parentElement) {
            e.currentTarget.parentElement.innerHTML = '<div class="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center border border-white/10 shadow-sm"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-white"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path><path d="m9 12 2 2 4-4"></path></svg></div><h1 class="text-xl font-bold tracking-tight text-white">FraudShield <span class="text-blue-400 font-normal">AI</span></h1>';
          }
        }} />
        <h1 className="text-xl font-bold tracking-tight text-white">
          FraudShield <span className="text-blue-400 font-normal">AI</span>
        </h1>
      </div>

      {currentUser ? (
        <div className="flex items-center space-x-6">
          <div className="relative">
            <button className="text-slate-400 hover:text-white transition-colors flex items-center">
              <Bell size={18} />
              {alertTransaction && (
                <span className="absolute top-0 right-0 w-2 h-2 bg-alert-red rounded-full ring-2 ring-navy-900"></span>
              )}
            </button>
          </div>
          
          <div className="h-6 w-px bg-white/10"></div>
          
          <div className="flex items-center space-x-3 group cursor-pointer">
            <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center border border-white/10 text-white text-sm font-medium">
              {currentUser.name.charAt(0)}
            </div>
            <div className="hidden md:block text-sm">
              <p className="font-medium text-white">{currentUser.name}</p>
              <p className="text-slate-400 text-xs capitalize">{currentUser.role}</p>
            </div>
            <button 
              onClick={handleLogout}
              className="ml-4 text-slate-500 hover:text-white transition-colors"
              title="Sign Out"
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      ) : (
        <div className="flex items-center space-x-4">
          <button 
            onClick={() => navigate('/login')}
            className="text-sm font-medium text-slate-300 hover:text-white transition-colors"
          >
            Sign In
          </button>
          <button 
            className="text-sm font-medium bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg transition-colors hidden sm:block"
          >
            Request Demo
          </button>
        </div>
      )}
    </header>
  );
}
