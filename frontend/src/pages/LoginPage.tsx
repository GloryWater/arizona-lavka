'use client';

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { LogIn, Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '@/features/auth/model/useAuthStore';
import { useToast } from '@/shared/ui/Toast';
import {
  Card,
  CardContent,
  Button,
  Input,
} from '@/shared/ui';

export function LoginPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const { login, isLoading } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    username_or_email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login(formData);
      toast.success('Вы успешно вошли в систему');
      navigate('/');
    } catch (error) {
      // Ошибка уже обработана в store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12 bg-gradient-to-br from-blue-500/10 via-background to-background">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <Card variant="elevated">
          <CardContent className="p-8">
            {/* Header */}
            <div className="text-center mb-8">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                className="mx-auto h-14 w-14 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-500/25 mb-4"
              >
                <LogIn className="h-7 w-7 text-white" />
              </motion.div>
              <h1 className="text-2xl font-bold text-foreground mb-2">
                С возвращением!
              </h1>
              <p className="text-sm text-muted-foreground">
                Войдите в свой аккаунт для продолжения
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Имя пользователя или Email"
                type="text"
                placeholder="username@example.com"
                value={formData.username_or_email}
                onChange={(e) =>
                  setFormData({ ...formData, username_or_email: e.target.value })
                }
                icon={<Mail className="h-5 w-5" />}
                required
              />

              <Input
                label="Пароль"
                type={showPassword ? 'text' : 'password'}
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                icon={<Lock className="h-5 w-5" />}
                iconPosition="right"
                required
              >
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5" />
                  ) : (
                    <Eye className="h-5 w-5" />
                  )}
                </button>
              </Input>

              <Button
                type="submit"
                className="w-full h-12 text-base"
                isLoading={isLoading}
                icon={<LogIn className="h-5 w-5" />}
              >
                {isLoading ? 'Вход...' : 'Войти'}
              </Button>
            </form>

            {/* Footer */}
            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Нет аккаунта?{' '}
                <Link
                  to="/register"
                  className="text-blue-500 hover:text-blue-600 font-medium transition-colors"
                >
                  Зарегистрироваться
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
