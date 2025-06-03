import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../utils/supabaseClient'
import NavBar from '../components/NavBar'
import MoodChart from '../components/MoodChart'
import axios from 'axios'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [moodData, setMoodData] = useState([])
  const [patterns, setPatterns] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    checkUser()
  }, [])

  useEffect(() => {
    if (user) {
      fetchData()
    }
  }, [user])

  const checkUser = async () => {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) {
      router.push('/login')
    } else {
      setUser(user)
    }
  }

  const fetchData = async () => {
    // Fetch mood data
    const { data, error } = await supabase
      .from('journal_entries')
      .select('created_at, mood_rating, sentiment_score')
      .eq('user_id', user.id)
      .order('created_at', { ascending: true })
      .gte('created_at', new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString())

    if (!error && data) {
      setMoodData(data)
    }

    // Fetch patterns from backend
    try {
      const response = await axios.get(`http://localhost:8000/api/trends/${user.id}`)
      setPatterns(response.data)
    } catch (error) {
      console.error('Error fetching patterns:', error)
    }
    
    setLoading(false)
  }

  const getDayOfWeekInsight = (pattern) => {
    const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    if (pattern && pattern.worst_day !== undefined) {
      return `Your mood tends to be lowest on ${days[pattern.worst_day]}s`
    }
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Your Mental Health Dashboard</h1>
        
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Analyzing your patterns...</p>
          </div>
        ) : (
          <div className="grid gap-8">
            {/* Mood Chart */}
            <div className="bg-white p-6 rounded-lg card-shadow">
              <h2 className="text-2xl font-semibold mb-4">Mood Trends (Last 30 Days)</h2>
              <MoodChart data={moodData} />
            </div>

            {/* Key Metrics */}
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-white p-6 rounded-lg card-shadow text-center">
                <div className="text-4xl font-bold text-blue-600 mb-2">
                  {patterns?.mh_index ? patterns.mh_index.toFixed(1) : '--'}
                </div>
                <p className="text-gray-600">Mental Health Index</p>
                <p className="text-sm text-gray-500 mt-1">Based on recent entries</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg card-shadow text-center">
                <div className="text-4xl font-bold text-green-600 mb-2">
                  {moodData.length > 0 ? 
                    (moodData.reduce((sum, entry) => sum + entry.mood_rating, 0) / moodData.length).toFixed(1) 
                    : '--'}
                </div>
                <p className="text-gray-600">Average Mood</p>
                <p className="text-sm text-gray-500 mt-1">Out of 10</p>
              </div>
              
              <div className="bg-white p-6 rounded-lg card-shadow text-center">
                <div className="text-4xl font-bold text-purple-600 mb-2">
                  {patterns?.dominant_cycle ? `${patterns.dominant_cycle.period}d` : '--'}
                </div>
                <p className="text-gray-600">Dominant Cycle</p>
                <p className="text-sm text-gray-500 mt-1">Detected pattern</p>
              </div>
            </div>

            {/* Pattern Analysis */}
            {patterns && (
              <div className="grid md:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-lg card-shadow">
                  <h3 className="text-xl font-semibold mb-4">🔄 Detected Patterns</h3>
                  <div className="space-y-3">
                    {patterns.weekly_pattern && (
                      <div className="p-3 bg-blue-50 rounded-lg">
                        <p className="font-medium text-blue-800">Weekly Pattern</p>
                        <p className="text-blue-600 text-sm">
                          {getDayOfWeekInsight(patterns.weekly_pattern)}
                        </p>
                      </div>
                    )}
                    
                    {patterns.fourier_peaks && patterns.fourier_peaks.length > 0 && (
                      <div className="p-3 bg-purple-50 rounded-lg">
                        <p className="font-medium text-purple-800">Cycle Detection</p>
                        <p className="text-purple-600 text-sm">
                          Strong {patterns.fourier_peaks[0].period.toFixed(1)}-day cycle detected
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="bg-white p-6 rounded-lg card-shadow">
                  <h3 className="text-xl font-semibold mb-4">💡 Insights & Recommendations</h3>
                  <div className="space-y-3">
                    {patterns.recommendations?.map((rec, idx) => (
                      <div key={idx} className="flex items-start">
                        <span className="text-green-500 mr-2 mt-1">✓</span>
                        <span className="text-gray-700 text-sm">{rec}</span>
                      </div>
                    )) || (
                      <p className="text-gray-500 text-sm">
                        Keep journaling to unlock personalized insights!
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Fourier Analysis Visualization */}
            {patterns?.fourier_analysis && (
              <div className="bg-white p-6 rounded-lg card-shadow">
                <h3 className="text-xl font-semibold mb-4">📊 Cycle Analysis</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="font-medium mb-2">Frequency Components</h4>
                    <div className="space-y-2">
                      {patterns.fourier_peaks.slice(0, 3).map((peak, idx) => (
                        <div key={idx} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <span className="text-sm">{peak.period.toFixed(1)} days</span>
                          <div className="w-24 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${(peak.amplitude / patterns.fourier_peaks[0].amplitude) * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Pattern Strength</h4>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-blue-600">
                        {((patterns.fourier_peaks[0]?.amplitude || 0) * 100).toFixed(0)}%
                      </div>
                      <p className="text-sm text-gray-600">Pattern Clarity</p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
  