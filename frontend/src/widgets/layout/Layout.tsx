'use client';

import React from 'react';
import { Header } from '@/widgets/header/Header';
import { Footer } from '@/widgets/footer/Footer';

interface LayoutProps {
  children: React.ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="relative flex min-h-screen flex-col">
      <a href="#main-content" className="skip-to-content">
        Перейти к основному контенту
      </a>
      <Header />
      <main id="main-content" className="flex-1" tabIndex={-1}>
        {children}
      </main>
      <Footer />
    </div>
  );
}
