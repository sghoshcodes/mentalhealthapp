import { useRouter } from 'next/router'
import { useEffect, useState } from 'react'
import { supabase } from '../utils/supabaseClient'
import NavBar from '../components/NavBar'

export default function Home() {
  const router = useRouter()
  const [user, setUser] = useState(null)

  useEffect(() => {
    checkUser()
  }, [])

  const checkUser = async () => {
    const { data: { user } } = await supabase.auth.getUser()
    setUser(user)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <NavBar />
      <main className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-800 mb-6">
            Track Your Mental Health Journey
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI-powered journaling with pattern detection to understand your emotional cycles
          </p>
          
          <div className="flex gap-4 justify-center">
            {user ? (
              <>
                <button 
                  onClick={() => router.push('/journal')}
                  className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Start Journaling
                </button>
                <button 
                  onClick={() => router.push('/dashboard')}
                  className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                  View Dashboard
                </button>
              </>
            ) : (
              <>
                <button 
                  onClick={() => router.push('/login')}
                  className="px-8 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                >
                  Login
                </button>
                <button 
                  onClick={() => router.push('/signup')}
                  className="px-8 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition"
                >
                  Sign Up
                </button>
              </>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-8 mt-16">
          <div className="bg-white p-6 rounded-lg card-shadow">
            <div className="text-4xl mb-4">📝</div>
            <h3 className="text-xl font-semibold mb-3">Daily Journaling</h3>
            <p className="text-gray-600">Express your thoughts and emotions in a safe, private space</p>
          </div>
          <div className="bg-white p-6 rounded-lg card-shadow">
            <div className="text-4xl mb-4">📊</div>
            <h3 className="text-xl font-semibold mb-3">Pattern Detection</h3>
            <p className="text-gray-600">Fourier analysis reveals hidden cycles in your mood patterns</p>
          </div>
          <div className="bg-white p-6 rounded-lg card-shadow">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-3">Personalized Insights</h3>
            <p className="text-gray-600">Get actionable advice based on your unique patterns</p>
          </div>
        </div>
      </main>
    </div>
  )
}