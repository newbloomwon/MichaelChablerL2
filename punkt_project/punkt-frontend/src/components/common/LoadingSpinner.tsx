import { FC } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

interface LoadingSpinnerProps {
    size?: number;
    className?: string;
    label?: string;
}

export const LoadingSpinner: FC<LoadingSpinnerProps> = ({ size = 24, className, label }) => {
    return (
        <div className={cn("flex flex-col items-center justify-center gap-3", className)}>
            <Loader2 className="animate-spin text-primary" size={size} />
            {label && <span className="text-sm text-gray-400 font-medium">{label}</span>}
        </div>
    );
};
