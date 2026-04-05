import React, { useEffect } from 'react';
import { Header } from './Header';
import { Footer } from './Footer';
import { AlertModal } from './AlertModal';
import { initAudio } from '../utils/mockDataGenerator';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  useEffect(() => {
    const handleFirstClick = () => {
       initAudio();
       window.removeEventListener('click', handleFirstClick);
    };
    window.addEventListener('click', handleFirstClick);
    return () => window.removeEventListener('click', handleFirstClick);
  }, []);

  return (
    <div className="flex flex-col min-h-screen bg-[#07111A] font-sans antialiased">
      <Header />
      
      <main className="flex-1 w-full relative pb-16">
        {/* Subtle background ambient light */}
        <div className="absolute top-[-20%] left-[20%] w-[40%] h-[40%] rounded-full bg-slate-500/5 blur-[120px] pointer-events-none -z-10"></div>
        <div className="absolute bottom-[-20%] right-[10%] w-[30%] h-[30%] rounded-full bg-[#1b344d]/10 blur-[100px] pointer-events-none -z-10"></div>
        
        {children}
      </main>

      <AlertModal />
      <Footer />
    </div>
  );
}
