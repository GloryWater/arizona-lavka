'use client';

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShoppingBag,
  User,
  LogOut,
  Menu,
  X,
  Sun,
  Moon,
  Shield,
  Home,
  Settings,
  FileText,
} from 'lucide-react';
import { useAuthStore } from '@/features/auth/model/useAuthStore';
import { useThemeStore } from '@/features/theme/model/useThemeStore';
import { Button } from '@/shared/ui/Button';
import { cn } from '@/shared/lib/utils';

interface NavLink {
  href: string;
  label: string;
  icon?: React.ReactNode;
}

const navLinks: NavLink[] = [
  { href: '/', label: 'Marketplace', icon: <Home className="h-4 w-4" aria-hidden="true" /> },
  { href: '/config-generator', label: 'Генератор', icon: <Settings className="h-4 w-4" aria-hidden="true" /> },
  { href: '/about', label: 'О проекте', icon: <FileText className="h-4 w-4" aria-hidden="true" /> },
];

const adminNavLinks: NavLink[] = [
  { href: '/admin', label: 'Админка', icon: <Shield className="h-4 w-4" aria-hidden="true" /> },
];

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated, isAdmin, logout } = useAuthStore();
  const { isDark, toggleTheme } = useThemeStore();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Close mobile menu on resize from mobile to desktop
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 768 && isMobileMenuOpen) {
        setIsMobileMenuOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMobileMenuOpen]);

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  const isActive = (href: string) => location.pathname === href;

  return (
    <header
      className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 transition-all duration-300"
      role="banner"
    >
      <div className="container flex h-16 max-w-screen-3xl items-center px-4 md:px-6">
        {/* Logo - Icon always visible, text on sm+ */}
        <Link to="/" className="mr-4 sm:mr-8 flex items-center space-x-2 sm:space-x-3 flex-shrink-0 group" aria-label="Arizona Lavka - главная страница">
          <motion.div
            whileHover={{ scale: 1.05, rotate: 5 }}
            whileTap={{ scale: 0.95 }}
            className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/25 flex-shrink-0 group-hover:shadow-xl group-hover:shadow-blue-500/30 transition-all duration-300"
          >
            <ShoppingBag className="h-5 w-5 text-white" aria-hidden="true" />
          </motion.div>
          <div className="hidden sm:block overflow-hidden">
            <span className="block text-lg font-bold text-foreground bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">Arizona Lavka</span>
            <span className="block text-xs text-muted-foreground">Marketplace v5.0</span>
          </div>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-1" aria-label="Основная навигация">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                'hover:bg-accent/50 hover:text-foreground',
                isActive(link.href)
                  ? 'bg-accent text-accent-foreground shadow-sm'
                  : 'text-muted-foreground'
              )}
              aria-current={isActive(link.href) ? 'page' : undefined}
            >
              {link.icon}
              {link.label}
            </Link>
          ))}
          {isAdmin && adminNavLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className={cn(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200',
                'hover:bg-accent/50 hover:text-foreground',
                isActive(link.href)
                  ? 'bg-accent text-accent-foreground shadow-sm'
                  : 'text-muted-foreground'
              )}
              aria-current={isActive(link.href) ? 'page' : undefined}
            >
              {link.icon}
              {link.label}
            </Link>
          ))}
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex ml-auto items-center space-x-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="h-10 w-10"
            aria-label={isDark ? 'Включить светлую тему' : 'Включить тёмную тему'}
          >
            {isDark ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
          </Button>

          {isAuthenticated ? (
            <>
              <Button
                variant="ghost"
                onClick={() => navigate('/profile')}
                className="gap-2"
              >
                <User className="h-4 w-4" aria-hidden="true" />
                <span className="font-medium">{user?.username}</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                icon={<LogOut className="h-4 w-4" aria-hidden="true" />}
              >
                Выход
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/login')}
              >
                Вход
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={() => navigate('/register')}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 border-0 shadow-lg shadow-blue-500/25"
              >
                Регистрация
              </Button>
            </>
          )}
        </div>

        {/* Mobile menu button */}
        <Button
          variant="ghost"
          size="icon"
          className="ml-auto md:hidden"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label={isMobileMenuOpen ? 'Закрыть меню' : 'Открыть меню'}
          aria-expanded={isMobileMenuOpen}
          aria-controls="mobile-menu"
        >
          {isMobileMenuOpen ? <X className="h-6 w-6" aria-hidden="true" /> : <Menu className="h-6 w-6" aria-hidden="true" />}
        </Button>
      </div>

      {/* Mobile Navigation */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="md:hidden border-t border-border"
            id="mobile-menu"
            role="navigation"
            aria-label="Мобильное меню"
          >
            <div className="container px-4 py-4 space-y-2">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                    isActive(link.href)
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                  )}
                  aria-current={isActive(link.href) ? 'page' : undefined}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  {link.icon}
                  {link.label}
                </Link>
              ))}
              {isAdmin && (
                <Link
                  to="/admin"
                  className={cn(
                    'flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                    isActive('/admin')
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                  )}
                  aria-current={isActive('/admin') ? 'page' : undefined}
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  <Shield className="h-4 w-4" aria-hidden="true" />
                  Админка
                </Link>
              )}

              <div className="pt-4 border-t border-border">
                <Button
                  variant="ghost"
                  className="w-full justify-start gap-3"
                  onClick={() => {
                    toggleTheme();
                    setIsMobileMenuOpen(false);
                  }}
                >
                  {isDark ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
                  <span>{isDark ? 'Светлая тема' : 'Тёмная тема'}</span>
                </Button>
              </div>

              {isAuthenticated ? (
                <div className="pt-4 border-t border-border space-y-2">
                  <Link
                    to="/profile"
                    className="flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
                    onClick={() => setIsMobileMenuOpen(false)}
                  >
                    <User className="h-5 w-5" aria-hidden="true" />
                    <span>{user?.username}</span>
                  </Link>
                  <Button
                    variant="outline"
                    className="w-full gap-2"
                    onClick={() => {
                      handleLogout();
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    <LogOut className="h-4 w-4" aria-hidden="true" />
                    Выход
                  </Button>
                </div>
              ) : (
                <div className="pt-4 border-t border-border space-y-2">
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => {
                      navigate('/login');
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    Вход
                  </Button>
                  <Button
                    variant="primary"
                    className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 border-0 shadow-lg shadow-blue-500/25"
                    onClick={() => {
                      navigate('/register');
                      setIsMobileMenuOpen(false);
                    }}
                  >
                    Регистрация
                  </Button>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
