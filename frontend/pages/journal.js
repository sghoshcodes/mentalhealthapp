import { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import { supabase } from '../utils/supabaseClient'
import NavBar from '../components/NavBar'
import JournalEntryForm from '../components/JournalEntryForm'
import axios from 'axios'

export default function Journal() {
  const router = useRouter()
  const [user, setUser] = useState(null)
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    checkUser()
  }, [])

  useEffect(() => {
    if (user) {
      fetchEntries()
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

  const fetchEntries = async () => {
    const { data, error } = await supabase
      .from('journal_entries')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(10)
    
    if (!error) setEntries(data || [])
  }

  const handleSubmit = async (content, mood) => {
    setLoading(true)
    try {
      // Get sentiment analysis from backend
      const sentimentResponse = await axios.post('http://localhost:8000/api/sentiment', {
        text: content
      })

      // Save to Supabase
      const { data, error } = await supabase
        .from('journal_entries')
        .insert([
          {
            user_id: user.id,
            content,
            mood_rating: mood,
            sentiment_score: sentimentResponse.data.sentiment_score,
            emotions: sentimentResponse.data.emotions
          }
        ])

      if (!error) {
        fetchEntries()
        
        // Calculate mental health score
        await axios.post('http://localhost:8000/api/score/calculate', {
          user_id: user.id
        })
      }
    } catch (error) {
      console.error('Error saving entry:', error)
    }
    setLoading(false)
  }

  const getEmotionEmoji = (emotions) => {
    if (!emotions) return '😐'
    const emotionMap = {
      joy: '😊',
      sadness: '😢',
      anger: '😠',
      fear: '😨',
      surprise: '😮',
      disgust: '🤢'
    }
    const topEmotion = Object.entries(emotions).reduce((a, b) => a[1] > b[1] ? a : b)[0]
    return emotionMap[topEmotion] || '😐'
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <NavBar />
      <main className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Your Journal</h1>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div>
            <JournalEntryForm onSubmit={handleSubmit} loading={loading} />
          </div>
          
          <div>
            <h2 className="text-2xl font-semibold mb-4">Recent Entries</h2>
            <div className="space-y-4">
              {entries.map((entry) => (
                <div key={entry.id} className="bg-white p-4 rounded-lg card-shadow">
                  <div className="flex justify-between items-start mb-2">
                    <span className="text-sm text-gray-500">
                      {new Date(entry.created_at).toLocaleDateString()}
                    </span>
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">{getEmotionEmoji(entry.emotions)}</span>
                      <span className="text-sm font-semibold">
                        Mood: {entry.mood_rating}/10
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-700 line-clamp-3">{entry.content}</p>
                  {entry.sentiment_score !== null && (
                    <div className="mt-2 text-sm text-gray-600">
                      Sentiment: {(entry.sentiment_score * 100).toFixed(0)}% positive
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}