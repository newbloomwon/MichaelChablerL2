import { FC } from 'react';
import { cn } from '../../lib/utils';

interface SkeletonProps {
    className?: string;
}

export const Skeleton: FC<SkeletonProps> = ({ className }) => {
    return (
        <div className={cn("animate-pulse bg-gray-800/50 rounded-lg", className)} />
    );
};
