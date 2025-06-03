import { useState } from 'react'

export default function JournalEntryForm({ onSubmit, loading }) {
  const [content, setContent] = useState('')
  const [mood, setMood] = useState(5)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (content.trim()) {
      await onSubmit(content, mood)
      setContent('')
      setMood(5)
    }
  }

  const getMoodEmoji = (value) => {
    const emojis = ['😢', '😔', '😕', '😐', '🙂', '😊', '😄', '😃', '😁', '🤩']
    return emojis[value - 1] || '😐'
  }

  const getMoodColor = (value) => {
    if (value <= 3) return 'text-red-500'
    if (value <= 6) return 'text-yellow-500'
    return 'text-green-500'
  }

  return (
    <div className="bg-white p-6 rounded-lg card-shadow">
      <h2 className="text-2xl font-semibold mb-4">How are you feeling today?</h2>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            What's on your mind?
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={6}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                      placeholder="Write about your day, feelings, thoughts, or anything that comes to mind..."
            required
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Rate your mood (1-10)
          </label>
          <div className="space-y-3">
            <div className="flex items-center justify-center space-x-2">
              <span className={`text-4xl ${getMoodColor(mood)}`}>
                {getMoodEmoji(mood)}
              </span>
              <span className="text-2xl font-bold text-gray-700">{mood}</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={mood}
              onChange={(e) => setMood(parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer mood-gradient"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>Very Low</span>
              <span>Neutral</span>
              <span>Very High</span>
            </div>
          </div>
        </div>
        
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
        >
          {loading ? 'Analyzing & Saving...' : 'Save Entry'}
        </button>
      </form>
    </div>
  )
}