import React, { useState } from 'react';
import { Menu, X, Home, ShoppingBag, Settings, User, Info, LogOut } from 'lucide-react';
import { useAuthStore } from '@/features/auth/model/useAuthStore';
import { cn } from '@/shared/lib/utils';

interface MobileMenuProps {
  className?: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
}

export function MobileMenu({ className }: MobileMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated, logout } = useAuthStore();

  const navItems: NavItem[] = [
    { label: 'Главная', href: '/', icon: <Home className="h-5 w-5" /> },
    { label: 'Лавки', href: '/lavka', icon: <ShoppingBag className="h-5 w-5" /> },
    { label: 'Генератор', href: '/config-generator', icon: <Settings className="h-5 w-5" /> },
    { label: 'О проекте', href: '/about', icon: <Info className="h-5 w-5" /> },
  ];

  if (isAuthenticated) {
    navItems.push({ label: 'Профиль', href: '/profile', icon: <User className="h-5 w-5" /> });
  }

  const handleLogout = async () => {
    await logout();
    setIsOpen(false);
    window.location.href = '/';
  };

  return (
    <div className={cn('relative', className)}>
      {/* Hamburger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-lg hover:bg-accent transition-colors"
        aria-label={isOpen ? 'Закрыть меню' : 'Открыть меню'}
        aria-expanded={isOpen}
        data-testid="hamburger-menu"
      >
        {isOpen ? (
          <X className="h-6 w-6" style={{ color: 'var(--foreground) !important' }} aria-hidden="true" />
        ) : (
          <Menu className="h-6 w-6" style={{ color: 'var(--foreground) !important' }} aria-hidden="true" />
        )}
      </button>

      {/* Mobile Navigation Menu */}
      {isOpen && (
        <div
          className="fixed inset-0 top-16 z-50 bg-background/95 backdrop-blur-sm animate-in slide-in-from-top-4 duration-200"
          role="dialog"
          aria-modal="true"
          aria-label="Мобильное меню"
          data-testid="mobile-nav"
        >
          <nav className="container mx-auto px-4 py-6">
            <ul className="space-y-2">
              {navItems.map((item) => (
                <li key={item.label}>
                  <a
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    className="flex items-center gap-4 px-4 py-4 rounded-lg hover:bg-accent transition-colors text-lg font-medium"
                  >
                    <span className="inline-flex" style={{ color: 'var(--foreground)' as React.CSSProperties['color'] }}>
                      {item.icon}
                    </span>
                    <span>{item.label}</span>
                  </a>
                </li>
              ))}

              {isAuthenticated && (
                <li className="pt-4 border-t border-border mt-4">
                  <button
                    onClick={handleLogout}
                    className="flex items-center gap-4 px-4 py-4 w-full rounded-lg hover:bg-destructive/10 text-destructive transition-colors text-lg font-medium"
                  >
                    <LogOut className="h-5 w-5" style={{ color: 'var(--destructive) !important' }} aria-hidden="true" />
                    <span>Выйти</span>
                  </button>
                </li>
              )}
            </ul>
          </nav>
        </div>
      )}
    </div>
  );
}

export default MobileMenu;
