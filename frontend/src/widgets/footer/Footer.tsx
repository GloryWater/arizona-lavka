'use client';

import { Link } from 'react-router-dom';
import {
  ShoppingBag,
  Heart,
  ExternalLink,
} from 'lucide-react';

const footerLinks = {
  marketplace: [
    { href: '/', label: 'Marketplace' },
    { href: '/config-generator', label: 'Генератор' },
  ],
  account: [
    { href: '/login', label: 'Вход' },
    { href: '/register', label: 'Регистрация' },
    { href: '/profile', label: 'Профиль' },
  ],
  info: [
    { href: '/about', label: 'О проекте', external: false },
  ],
};

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-border/50 bg-muted/30 backdrop-blur-xl" role="contentinfo">
      <div className="container max-w-screen-3xl px-4 md:px-6 py-8 md:py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <Link to="/" className="flex items-center space-x-3 mb-4 group" aria-label="Arizona Lavka - главная страница">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 shadow-lg shadow-blue-500/25 group-hover:shadow-xl group-hover:shadow-blue-500/30 transition-all duration-300">
                <ShoppingBag className="h-5 w-5 text-white" aria-hidden="true" />
              </div>
              <div>
                <span className="block text-lg font-bold text-foreground bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">Arizona Lavka</span>
                <span className="block text-xs text-muted-foreground">Marketplace</span>
              </div>
            </Link>
            <p className="text-sm text-muted-foreground mb-4 leading-relaxed">
              Мониторинг и автоматизация торговли для Arizona RP
            </p>
          </div>

          {/* Marketplace */}
          <nav aria-label="Marketplace навигация">
            <h3 className="text-sm font-semibold text-foreground mb-3">Marketplace</h3>
            <ul className="space-y-2">
              {footerLinks.marketplace.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200 hover:underline hover:underline-offset-2"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Account */}
          <nav aria-label="Аккаунт навигация">
            <h3 className="text-sm font-semibold text-foreground mb-3">Аккаунт</h3>
            <ul className="space-y-2">
              {footerLinks.account.map((link) => (
                <li key={link.href}>
                  <Link
                    to={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200 hover:underline hover:underline-offset-2"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* Info */}
          <nav aria-label="Информация навигация">
            <h3 className="text-sm font-semibold text-foreground mb-3">Информация</h3>
            <ul className="space-y-2">
              {footerLinks.info.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target={link.external ? '_blank' : undefined}
                    rel={link.external ? 'noopener noreferrer' : undefined}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200 flex items-center gap-1 hover:underline hover:underline-offset-2"
                    {...(link.external ? { 'aria-label': `${link.label} (открывается в новой вкладке)` } : {})}
                  >
                    {link.label}
                    {link.external && <ExternalLink className="h-3 w-3" aria-hidden="true" />}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>

        {/* Bottom bar */}
        <div className="mt-8 pt-8 border-t border-border/50 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © {currentYear} Arizona Lavka Marketplace. Все права защищены.
          </p>
          <p className="text-sm text-muted-foreground flex items-center gap-1">
            Сделано с <Heart className="h-3 w-3 text-red-500 fill-red-500 animate-pulse" aria-hidden="true" /> для сообщества
          </p>
        </div>
      </div>
    </footer>
  );
}
