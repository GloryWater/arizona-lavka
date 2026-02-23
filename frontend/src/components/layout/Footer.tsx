import React from 'react';
import { ShoppingBag } from 'lucide-react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-dark-card border-t border-dark-border mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2">
            <ShoppingBag className="h-6 w-6 text-primary-500" />
            <span className="text-gray-300">Arizona Lavka Marketplace</span>
          </div>
          
          <div className="text-gray-400 text-sm">
            © {currentYear} Arizona Lavka. Все права защищены.
          </div>
          
          <div className="flex items-center space-x-4 text-sm text-gray-400">
            <span>v3.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
