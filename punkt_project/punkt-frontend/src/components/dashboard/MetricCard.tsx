import { FC } from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
    name: string;
    value: string | number;
    icon: LucideIcon;
    color: string;
    trend?: {
        value: string;
        positive: boolean;
    };
    loading?: boolean;
}

const ColorMap: Record<string, string> = {
    blue: 'bg-blue-100 text-blue-600 border-blue-600',
    green: 'bg-green-100 text-green-600 border-green-600',
    yellow: 'bg-yellow-100 text-yellow-600 border-yellow-600',
    red: 'bg-red-100 text-red-600 border-red-600',
    purple: 'bg-purple-100 text-purple-600 border-purple-600',
    indigo: 'bg-indigo-100 text-indigo-600 border-indigo-600',
};

export const MetricCard: FC<MetricCardProps> = ({
    name,
    value,
    icon: Icon,
    color,
    trend,
    loading
}) => {
    if (loading) {
        return (
            <div className="bg-secondary p-6 rounded-2xl border border-gray-800 shadow-lg animate-pulse">
                <div className="flex items-center justify-between mb-4">
                    <div className="p-3 rounded-xl bg-gray-900/50 w-12 h-12" />
                    <div className="h-4 w-12 bg-gray-800 rounded-full" />
                </div>
                <div className="h-4 w-24 bg-gray-800 rounded mb-2" />
                <div className="h-8 w-16 bg-gray-800 rounded" />
            </div>
        );
    }

    return (
        <div className="glass-panel hover:scale-[1.02] transition-transform duration-300">
            <div className="tape-strip"></div>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm font-typewriter text-gray-500 uppercase tracking-wider">{name}</p>
                    <p className="mt-2 text-3xl font-marker text-ink -rotate-1">{value}</p>
                    {trend && (
                        <p className={`mt-2 text-sm font-bold font-typewriter ${trend.positive ? 'text-success' : 'text-error'}`}>
                            {trend.positive ? '+' : ''}{trend.value}
                        </p>
                    )}
                </div>
                <div className={`p-3 rounded-full border-2 border-ink ${ColorMap[color] || 'bg-gray-100 text-gray-600'}`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>
        </div>
    );
};
