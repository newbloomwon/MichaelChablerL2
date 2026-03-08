import { FC } from 'react';
import { AlertCircle, XCircle, RefreshCcw } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ErrorBannerProps {
    message: string;
    details?: string;
    onRetry?: () => void;
    onClose?: () => void;
    className?: string;
    variant?: 'error' | 'warning';
}

export const ErrorBanner: FC<ErrorBannerProps> = ({
    message,
    details,
    onRetry,
    onClose,
    className,
    variant = 'error'
}) => {
    return (
        <div className={cn(
            "p-4 rounded-xl border flex gap-4 transition-all animate-in slide-in-from-top duration-300",
            variant === 'error'
                ? "bg-error/10 border-error/20 text-error"
                : "bg-warning/10 border-warning/20 text-warning",
            className
        )}>
            <div className="shrink-0 mt-0.5">
                {variant === 'error' ? <XCircle size={20} /> : <AlertCircle size={20} />}
            </div>

            <div className="flex-1 min-w-0">
                <h3 className="text-sm font-bold uppercase tracking-wider">{message}</h3>
                {details && <p className="text-xs mt-1 opacity-80 break-words">{details}</p>}

                {onRetry && (
                    <button
                        onClick={onRetry}
                        className="mt-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest hover:underline"
                    >
                        <RefreshCcw size={12} />
                        Try Again
                    </button>
                )}
            </div>

            {onClose && (
                <button
                    onClick={onClose}
                    className="shrink-0"
                >
                    <XCircle size={20} className="opacity-50 hover:opacity-100" />
                </button>
            )}
        </div>
    );
};
