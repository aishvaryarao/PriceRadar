import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'

export const PriceChart = ({ data = [], isGenuineDeal = false }) => {
  if (!data || data.length === 0) {
    return (
      <div style={{
        width: '100%',
        height: '400px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #334155',
        color: '#94a3b8'
      }}>
        No price history available
      </div>
    )
  }

  return (
    <div style={{ width: '100%', height: '400px', backgroundColor: '#1e293b', borderRadius: '8px', padding: '16px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="scraped_at"
            stroke="#64748b"
            tickFormatter={(date) => new Date(date).toLocaleDateString()}
          />
          <YAxis stroke="#64748b" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '6px',
              color: '#e2e8f0'
            }}
            formatter={(value) => `₹${value}`}
            labelFormatter={(label) => new Date(label).toLocaleDateString()}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="price"
            stroke="#3b82f6"
            fillOpacity={1}
            fill="url(#colorPrice)"
            name="Current Price"
            strokeWidth={2}
          />
          {data[0]?.avg_7d && (
            <Line
              type="monotone"
              dataKey="avg_7d"
              stroke="#f97316"
              strokeDasharray="5 5"
              name="7-Day Avg"
              strokeWidth={1}
              dot={false}
            />
          )}
          {data[0]?.avg_30d && (
            <Line
              type="monotone"
              dataKey="avg_30d"
              stroke="#ef4444"
              strokeDasharray="5 5"
              name="30-Day Avg"
              strokeWidth={1}
              dot={false}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
