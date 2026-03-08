import { FC } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';
import { format } from 'date-fns';

interface TimeSeriesData {
    timestamp: string;
    INFO: number;
    WARN: number;
    ERROR: number;
    DEBUG: number;
    CRITICAL: number;
}

interface TimeSeriesChartProps {
    data: TimeSeriesData[];
    height?: number | string;
}

const COLORS = {
    INFO: '#3b82f6',
    WARN: '#f59e0b',
    ERROR: '#ef4444',
    DEBUG: '#6b7280',
    CRITICAL: '#dc2626',
};

export const TimeSeriesChart: FC<TimeSeriesChartProps> = ({ data, height = 300 }) => {
    return (
        <div className="w-full bg-secondary p-6 rounded-2xl border border-gray-800 shadow-xl overflow-hidden">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h3 className="text-lg font-bold text-white tracking-tight">Log Volume Over Time</h3>
                    <p className="text-xs text-gray-500 uppercase tracking-widest mt-1">Aggregated by log level</p>
                </div>
            </div>

            <div style={{ width: '100%', height }}>
                <ResponsiveContainer>
                    <AreaChart
                        data={data}
                        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                        <defs>
                            {Object.entries(COLORS).map(([key, color]) => (
                                <linearGradient key={key} id={`gradient-${key}`} x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={color} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={color} stopOpacity={0} />
                                </linearGradient>
                            ))}
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                        <XAxis
                            dataKey="timestamp"
                            stroke="#4b5563"
                            fontSize={10}
                            tickFormatter={(str) => format(new Date(str), 'HH:mm')}
                            axisLine={false}
                            tickLine={false}
                        />
                        <YAxis
                            stroke="#4b5563"
                            fontSize={10}
                            axisLine={false}
                            tickLine={false}
                        />
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#ffffff',
                                border: '2px solid #111111',
                                borderRadius: '4px',
                                boxShadow: '3px 3px 0px 0px rgba(0,0,0,1)',
                                fontSize: '12px',
                                fontFamily: 'Courier Prime, monospace',
                                color: '#111111',
                            }}
                            itemStyle={{ color: '#111111' }}
                            labelStyle={{ color: '#111111', fontWeight: 'bold', marginBottom: '4px' }}
                            labelFormatter={(label) => format(new Date(label), 'yyyy-MM-dd HH:mm:ss')}
                        />
                        <Legend
                            verticalAlign="top"
                            align="right"
                            iconType="circle"
                            wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px', paddingBottom: '20px' }}
                        />

                        {Object.entries(COLORS).map(([key, color]) => (
                            <Area
                                key={key}
                                type="monotone"
                                dataKey={key}
                                stroke={color}
                                fillOpacity={1}
                                fill={`url(#gradient-${key})`}
                                strokeWidth={2}
                                stackId="1"
                            />
                        ))}
                    </AreaChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
