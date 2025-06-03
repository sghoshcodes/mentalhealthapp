import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { format } from 'date-fns'

export default function MoodChart({ data }) {
  const processedData = data.map(entry => ({
    date: format(new Date(entry.created_at), 'MMM dd'),
    mood: entry.mood_rating,
    sentiment: entry.sentiment_score ? (entry.sentiment_score * 10) : null,
    fullDate: entry.created_at
  }))

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border rounded-lg shadow">
          <p className="font-medium">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.dataKey === 'mood' ? 'Mood: ' : 'Sentiment: '}
              {entry.value?.toFixed(1)}/10
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (!data.length) {
    return (
      <div className="h-64 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="text-6xl mb-4">📊</div>
          <p>No data yet. Start journaling to see your trends!</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={processedData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 10]} />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          <Area
            type="monotone"
            dataKey="mood"
            stroke="#3B82F6"
            fill="#3B82F6"
            fillOpacity={0.3}
            name="Mood Rating"
          />
          <Line
            type="monotone"
            dataKey="sentiment"
            stroke="#8B5CF6"
            strokeWidth={2}
            dot={{ r: 4 }}
            name="AI Sentiment"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}