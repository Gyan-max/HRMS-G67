import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface TrendData {
  timestamp: string;
  mood_score: number;
  sleep_hours: number;
  social_interactions: number;
  risk_score: number;
  risk_level: string;
}

interface TrendChartsProps {
  data: TrendData[];
}

export function TrendCharts({ data }: TrendChartsProps) {
  if (!data || data.length === 0) return null;

  // Format dates for display
  const chartData = data.map(d => ({
    ...d,
    displayDate: new Date(d.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' }),
  })).sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="grid gap-6 md:grid-cols-2">
      {/* Mood Trend */}
      <Card className="col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">🎭 Mood Trend (1-10)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis 
                  dataKey="displayDate" 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  domain={[0, 10]}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                  itemStyle={{ color: '#6366f1' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="mood_score" 
                  stroke="#6366f1" 
                  strokeWidth={3} 
                  dot={{ fill: '#6366f1', strokeWidth: 2 }} 
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Sleep Trend */}
      <Card className="col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">😴 Sleep Hours</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorSleep" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#22d3ee" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis 
                  dataKey="displayDate" 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  domain={[0, 12]}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                  itemStyle={{ color: '#22d3ee' }}
                />
                <ReferenceLine y={7} label={{ value: 'Target', position: 'right', fill: '#10b981', fontSize: 10 }} stroke="#10b981" strokeDasharray="3 3" />
                <Area 
                  type="monotone" 
                  dataKey="sleep_hours" 
                  stroke="#22d3ee" 
                  fillOpacity={1} 
                  fill="url(#colorSleep)" 
                  strokeWidth={3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Social Interactions */}
      <Card className="col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">🤝 Social Contact</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis 
                  dataKey="displayDate" 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                />
                <Bar dataKey="social_interactions" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={entry.social_interactions <= 1 ? '#fb7185' : entry.social_interactions <= 3 ? '#f59e0b' : '#10b981'} 
                      fillOpacity={0.8}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Risk Score */}
      <Card className="col-span-1">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">⚡ Risk Intensity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[200px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis 
                  dataKey="displayDate" 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                />
                <YAxis 
                  stroke="#888" 
                  fontSize={12} 
                  tickLine={false} 
                  axisLine={false} 
                  domain={[0, 1]}
                />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333', borderRadius: '8px' }}
                  itemStyle={{ color: '#fb7185' }}
                />
                <ReferenceLine y={0.65} label={{ value: 'High', position: 'right', fill: '#fb7185', fontSize: 10 }} stroke="#fb7185" strokeDasharray="3 3" />
                <ReferenceLine y={0.35} label={{ value: 'Mid', position: 'right', fill: '#f59e0b', fontSize: 10 }} stroke="#f59e0b" strokeDasharray="3 3" />
                <Line 
                  type="stepAfter" 
                  dataKey="risk_score" 
                  stroke="#fb7185" 
                  strokeWidth={2} 
                  dot={{ fill: '#fb7185', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
