import { useEffect, useRef, useCallback } from 'react';
import { Turnstile, type TurnstileInstance } from '@marsidev/react-turnstile';

interface TurnstileWidgetProps {
  onTokenChange: (token: string | null) => void;
  onError?: (error: string) => void;
}

/**
 * Cloudflare Turnstile Widget Component
 * 
 * Invisible CAPTCHA alternative that verifies users in the background.
 * 99% of legitimate users pass without any interaction.
 */
export function TurnstileWidget({ onTokenChange, onError }: TurnstileWidgetProps) {
  const widgetRef = useRef<TurnstileInstance | null>(null);
  const turnstileSiteKey = import.meta.env.VITE_CLOUDFLARE_TURNSTILE_SITE_KEY;

  const handleTokenChange = useCallback((token: string) => {
    onTokenChange(token);
  }, [onTokenChange]);

  const handleError = useCallback((error: string) => {
    console.error('Turnstile error:', error);
    onError?.(`Captcha verification failed: ${error}`);
  }, [onError]);

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      widgetRef.current?.remove();
    };
  }, []);

  // Skip rendering if site key is not configured (development mode)
  if (!turnstileSiteKey) {
    console.warn('Turnstile site key not configured. Using mock verification.');
    // In development without key, provide a mock token
    useEffect(() => {
      onTokenChange('mock-turnstile-token-dev');
    }, [onTokenChange]);
    
    return null;
  }

  return (
    <div className="flex justify-center my-4">
      <Turnstile
        ref={widgetRef}
        siteKey={turnstileSiteKey}
        onSuccess={handleTokenChange}
        onError={handleError}
      />
    </div>
  );
}
