import { FC } from 'react';
import {
    PieChart,
    Pie,
    Cell,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';

interface AggregationItem {
    name: string;
    value: number;
}

interface AggregationChartProps {
    data: AggregationItem[];
    type: 'pie' | 'bar';
    title: string;
    height?: number | string;
}

const COLORS = [
    '#8b5cf6', // primary
    '#3b82f6', // blue
    '#ec4899', // pink
    '#10b981', // green
    '#f59e0b', // amber
    '#06b6d4', // cyan
];

export const AggregationChart: FC<AggregationChartProps> = ({ data, type, title, height = 300 }) => {
    return (
        <div className="w-full h-full bg-secondary p-6 rounded-2xl border border-gray-800 shadow-xl overflow-hidden flex flex-col">
            <div className="mb-6">
                <h3 className="text-lg font-bold text-white tracking-tight">{title}</h3>
                <p className="text-xs text-gray-500 uppercase tracking-widest mt-1">Search Aggregation Result</p>
            </div>

            <div className="flex-1 min-h-0">
                <ResponsiveContainer width="100%" height={height}>
                    {type === 'pie' ? (
                        <PieChart>
                            <Pie
                                data={data}
                                cx="50%"
                                cy="50%"
                                innerRadius={60}
                                outerRadius={80}
                                fill="#8884d8"
                                paddingAngle={5}
                                dataKey="value"
                                stroke="none"
                            >
                                {data.map((_, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: '#ffffff',
                                    border: '2px solid #111111',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontFamily: 'Courier Prime, monospace',
                                    color: '#111111',
                                    boxShadow: '3px 3px 0px 0px rgba(0,0,0,1)',
                                }}
                                itemStyle={{ color: '#111111' }}
                                labelStyle={{ color: '#111111', fontWeight: 'bold' }}
                            />
                            <Legend
                                verticalAlign="bottom"
                                align="center"
                                iconType="circle"
                                wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', paddingTop: '20px' }}
                            />
                        </PieChart>
                    ) : (
                        <BarChart
                            data={data}
                            layout="vertical"
                            margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={true} vertical={false} />
                            <XAxis type="number" hide />
                            <YAxis
                                dataKey="name"
                                type="category"
                                stroke="#4b5563"
                                fontSize={10}
                                axisLine={false}
                                tickLine={false}
                                width={60}
                            />
                            <Tooltip
                                cursor={{ fill: '#ffffff05' }}
                                contentStyle={{
                                    backgroundColor: '#ffffff',
                                    border: '2px solid #111111',
                                    borderRadius: '4px',
                                    fontSize: '12px',
                                    fontFamily: 'Courier Prime, monospace',
                                    color: '#111111',
                                    boxShadow: '3px 3px 0px 0px rgba(0,0,0,1)',
                                }}
                                itemStyle={{ color: '#111111' }}
                                labelStyle={{ color: '#111111', fontWeight: 'bold' }}
                            />
                            <Bar
                                dataKey="value"
                                radius={[0, 4, 4, 0]}
                                barSize={20}
                            >
                                {data.map((_, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Bar>
                        </BarChart>
                    )}
                </ResponsiveContainer>
            </div>
        </div>
    );
};
