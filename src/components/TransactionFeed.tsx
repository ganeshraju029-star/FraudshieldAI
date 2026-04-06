import React from 'react';
import { useStore } from '../store';
import { motion, AnimatePresence } from 'framer-motion';
import { AlertCircle, CheckCircle2, AlertTriangle } from 'lucide-react';
import clsx from 'clsx';
import { formatCurrency } from '../utils/formatCurrency';

export function TransactionFeed() {
  const { transactions, userCurrency } = useStore();

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel rounded-2xl overflow-hidden flex flex-col h-full"
    >
      <div className="p-6 border-b border-white/5 flex justify-between items-center bg-navy-800/80 sticky top-0 z-10 w-full backdrop-blur-xl">
        <h3 className="text-lg font-semibold text-white">Live Transaction Stream</h3>
        <div className="flex space-x-2 text-xs">
          <span className="flex items-center"><div className="w-2 h-2 rounded-full bg-alert-green mr-1"></div>Safe</span>
          <span className="flex items-center ml-3"><div className="w-2 h-2 rounded-full bg-alert-yellow mr-1"></div>Review</span>
          <span className="flex items-center ml-3"><div className="w-2 h-2 rounded-full bg-alert-red mr-1"></div>Fraud</span>
        </div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar p-0 m-0">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="text-slate-400 bg-navy-900/50 sticky top-0 z-10 backdrop-blur-sm">
            <tr>
              <th className="px-6 py-4 font-medium">Status</th>
              <th className="px-6 py-4 font-medium">Transaction ID</th>
              <th className="px-6 py-4 font-medium">Amount</th>
              <th className="px-6 py-4 font-medium">Merchant Cat.</th>
              <th className="px-6 py-4 font-medium">Location</th>
              <th className="px-6 py-4 font-medium text-alert-red italic uppercase tracking-tighter">Reason</th>
              <th className="px-6 py-4 font-medium">Risk Score</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5 relative">
            <AnimatePresence initial={false}>
              {transactions.slice(0, 50).map((tx) => (
                <motion.tr 
                  key={tx.id}
                  initial={{ opacity: 0, y: -20, backgroundColor: 'rgba(255,255,255,0.1)' }}
                  animate={{ opacity: 1, y: 0, backgroundColor: 'rgba(0,0,0,0)' }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                  className={clsx(
                    "hover:bg-white/5 transition-colors group cursor-default",
                    tx.isFraud ? "bg-alert-red/5 hover:bg-alert-red/10" : ""
                  )}
                >
                  <td className="px-6 py-4">
                    {tx.status === 'safe' && <CheckCircle2 size={18} className="text-alert-green" />}
                    {tx.status === 'suspicious' && <AlertTriangle size={18} className="text-alert-yellow" />}
                    {tx.status === 'fraud' && (
                      <span className="relative flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-alert-red opacity-75"></span>
                        <AlertCircle size={16} className="relative inline-flex rounded-full text-alert-red" />
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono text-xs text-slate-300">{tx.id}</td>
                  <td className={clsx("px-6 py-4 font-medium", tx.isFraud ? "text-white" : "text-slate-200")}>
                    {formatCurrency(tx.amount, userCurrency)}
                  </td>
                  <td className="px-6 py-4 text-slate-400">{tx.category}</td>
                  <td className="px-6 py-4 text-slate-400 truncate max-w-[150px]">{tx.location}</td>
                  <td className="px-6 py-4 text-alert-red font-mono text-[10px] uppercase tracking-tighter">{tx.flagReason || '-'}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center">
                      <div className="w-16 h-2 bg-navy-900 rounded-full overflow-hidden mr-3 border border-white/5">
                        <div 
                          className={clsx(
                            "h-full rounded-full transition-all duration-1000 ease-out",
                            tx.riskScore > 75 ? "bg-alert-red" : tx.riskScore > 30 ? "bg-alert-yellow" : "bg-alert-green"
                          )}
                          style={{ width: `${tx.riskScore}%` }}
                        ></div>
                      </div>
                      <span className={clsx(
                         "font-mono text-xs font-medium w-8",
                         tx.riskScore > 75 ? "text-alert-red" : "text-slate-400"
                      )}>
                        {tx.riskScore}
                      </span>
                    </div>
                  </td>
                </motion.tr>
              ))}
            </AnimatePresence>
          </tbody>
        </table>
        {transactions.length === 0 && (
           <div className="flex flex-col items-center justify-center p-12 text-slate-500">
             <div className="w-8 h-8 border-2 border-slate-500 border-t-transparent rounded-full animate-spin mb-4"></div>
             <p>Awaiting transaction stream...</p>
           </div>
        )}
      </div>
    </motion.div>
  );
}
