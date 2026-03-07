/**
 * Arizona Lavka Marketplace - Main Application Component.
 *
 * © 2026 Arizona Lavka Marketplace. All Rights Reserved.
 * License: Proprietary Commercial License
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryProvider, ThemeProvider } from '@/app/providers';
import { Layout } from '@/widgets/layout';
import { useAuthStore } from '@/features/auth/model/useAuthStore';
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary';
import {
  HomePage,
  LavkaPage,
  ConfigGeneratorPage,
  LoginPage,
  RegisterPage,
  ProfilePage,
  AboutPage,
  AdminDashboard,
  AdminUsersPage,
  AdminLogsPage,
  AdminSettingsPage,
  MaintenancePage,
} from '@/pages';
import { ToastContainer } from '@/shared/ui/Toast';

// Layout для админки
function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-muted/30">
      <div className="border-b border-border bg-background">
        <div className="container flex h-16 items-center px-4 md:px-6 gap-4">
          <a href="/" className="text-lg font-bold text-foreground hover:text-primary transition-colors">
            ← На главную
          </a>
          <nav className="flex items-center gap-2 ml-auto">
            <a href="/admin" className="px-3 py-2 text-sm font-medium rounded-lg hover:bg-accent transition-colors">
              Dashboard
            </a>
            <a href="/admin/users" className="px-3 py-2 text-sm font-medium rounded-lg hover:bg-accent transition-colors">
              Пользователи
            </a>
            <a href="/admin/logs" className="px-3 py-2 text-sm font-medium rounded-lg hover:bg-accent transition-colors">
              Логи
            </a>
            <a href="/admin/settings" className="px-3 py-2 text-sm font-medium rounded-lg hover:bg-accent transition-colors">
              Настройки
            </a>
          </nav>
        </div>
      </div>
      {children}
    </div>
  );
}

// Защищённый роут для админки
function AdminProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, isLoading } = useAuthStore();

  // Показываем загрузку во время проверки
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-4 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <p className="text-muted-foreground">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Проверка авторизации
  if (!isAuthenticated) {
    window.location.href = '/login';
    return null;
  }

  // Проверка роли администратора
  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center p-6">
          <h1 className="text-2xl font-bold text-foreground mb-2">Доступ запрещён</h1>
          <p className="text-muted-foreground mb-4">У вас нет прав для доступа к этой странице</p>
          <a href="/" className="text-primary hover:underline">← На главную</a>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <QueryProvider>
          <ThemeProvider defaultTheme="dark">
            <Routes>
              {/* Admin Routes */}
              <Route
                path="/admin"
                element={
                  <AdminProtectedRoute>
                    <AdminLayout>
                      <AdminDashboard />
                    </AdminLayout>
                  </AdminProtectedRoute>
                }
              />
              <Route
                path="/admin/users"
                element={
                  <AdminProtectedRoute>
                    <AdminLayout>
                      <AdminUsersPage />
                    </AdminLayout>
                  </AdminProtectedRoute>
                }
              />
              <Route
                path="/admin/logs"
                element={
                  <AdminProtectedRoute>
                    <AdminLayout>
                      <AdminLogsPage />
                    </AdminLayout>
                  </AdminProtectedRoute>
                }
              />
              <Route
                path="/admin/settings"
                element={
                  <AdminProtectedRoute>
                    <AdminLayout>
                      <AdminSettingsPage />
                    </AdminLayout>
                  </AdminProtectedRoute>
                }
              />

              {/* Maintenance Page */}
              <Route
                path="/maintenance"
                element={<MaintenancePage />}
              />

              {/* Public Routes */}
              <Route
                path="/"
                element={
                  <Layout>
                    <HomePage />
                  </Layout>
                }
              />
              <Route
                path="/lavka/:lavkaUid"
                element={
                  <Layout>
                    <LavkaPage />
                  </Layout>
                }
              />
              <Route
                path="/config-generator"
                element={
                  <Layout>
                    <ConfigGeneratorPage />
                  </Layout>
                }
              />
              <Route
                path="/login"
                element={
                  <Layout>
                    <LoginPage />
                  </Layout>
                }
              />
              <Route
                path="/register"
                element={
                  <Layout>
                    <RegisterPage />
                  </Layout>
                }
              />
              <Route
                path="/profile"
                element={
                  <Layout>
                    <ProfilePage />
                  </Layout>
                }
              />
              <Route
                path="/about"
                element={
                  <Layout>
                    <AboutPage />
                  </Layout>
                }
              />
            </Routes>
            <ToastContainer />
          </ThemeProvider>
        </QueryProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
