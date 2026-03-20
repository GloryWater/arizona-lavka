import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { CheckCircle, XCircle, Mail } from 'lucide-react';
import { authApi } from '@/shared/api';
import { Card, Button } from '@/shared/ui';
import { useToast } from '@/shared/ui/Toast';

/**
 * Email Verification Page
 * 
 * Handles email verification from link: /verify?token=abc123
 */
export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const toast = useToast();
  const [isVerifying, setIsVerifying] = useState(true);
  
  const token = searchParams.get('token');
  
  const verifyMutation = useMutation({
    mutationFn: authApi.verifyEmailByToken,
    onSuccess: () => {
      toast.success('Email успешно подтверждён!');
      setIsVerifying(false);
      setTimeout(() => navigate('/'), 2000);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Ошибка верификации');
      setIsVerifying(false);
    },
  });
  
  useEffect(() => {
    if (token) {
      verifyMutation.mutate({ token });
    } else {
      toast.error('Токен верификации не найден');
      setIsVerifying(false);
      setTimeout(() => navigate('/register'), 2000);
    }
  }, [token]);
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500/5 via-background to-background px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <Card variant="elevated" className="border-border/50">
          <div className="p-8 text-center">
            {isVerifying ? (
              <>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                  className="mx-auto mb-6"
                >
                  <div className="relative">
                    <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mx-auto"></div>
                  </div>
                </motion.div>
                <h2 className="text-xl font-semibold mb-2 text-foreground">
                  Подтверждение email...
                </h2>
                <p className="text-muted-foreground">
                  Пожалуйста, подождите
                </p>
              </>
            ) : verifyMutation.isSuccess ? (
              <>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                  className="mx-auto mb-6"
                >
                  <CheckCircle className="h-16 w-16 text-green-500" />
                </motion.div>
                <h2 className="text-xl font-semibold mb-2 text-foreground">
                  Email подтверждён!
                </h2>
                <p className="text-muted-foreground mb-6">
                  Перенаправление на главную...
                </p>
              </>
            ) : (
              <>
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                  className="mx-auto mb-6"
                >
                  <XCircle className="h-16 w-16 text-red-500" />
                </motion.div>
                <h2 className="text-xl font-semibold mb-2 text-foreground">
                  Ошибка верификации
                </h2>
                <p className="text-muted-foreground mb-6">
                  {verifyMutation.error?.message || 'Ссылка верификации недействительна или истекла'}
                </p>
                <Button
                  onClick={() => navigate('/register')}
                  className="w-full"
                  icon={<Mail className="h-5 w-5" />}
                >
                  Вернуться к регистрации
                </Button>
              </>
            )}
          </div>
        </Card>
      </motion.div>
    </div>
  );
}
