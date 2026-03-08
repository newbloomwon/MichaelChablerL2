import React from 'react'
import { Link } from 'react-router-dom'
import ChatSkeleton from '../components/ChatSkeleton'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50">
      <div className="max-w-5xl mx-auto py-12 px-4">
        <section className="text-center space-y-4 mb-16">
          <h1 className="text-6xl font-bold text-gray-800">Learn Spanish</h1>
          <p className="text-2xl text-orange-500 font-semibold">Rediscover language learning with visual immersion</p>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto mt-4">
            Master vocabulary through images and sounds. Think in Spanish from day one—no translations, just pure immersion.
          </p>
        </section>

        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-800 mb-8">Your Lessons</h2>
          
          <Link
            to="/day-two"
            className="block bg-gradient-to-br from-orange-500 to-orange-600 text-white rounded-2xl overflow-hidden hover:shadow-2xl transition-shadow hover:to-orange-700"
          >
            <div className="p-8 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-3xl font-bold">Vocabulary Lesson</h3>
                <span className="text-5xl">📚</span>
              </div>
              <p className="text-lg text-orange-100">Learn Spanish vocabulary through images and sounds. Visual-first immersion with 10 common words.</p>
              <div className="flex items-center justify-between pt-4 border-t border-orange-400">
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-orange-100">10 vocabulary cards • Beginner Level</div>
                  <div className="text-sm font-semibold text-orange-200">~10 minutes</div>
                </div>
                <div className="text-2xl">→</div>
              </div>
            </div>
          </Link>
        </section>

        <section className="bg-blue-50 rounded-2xl p-8 border border-blue-200 mb-16">
          <h2 className="text-2xl font-bold text-blue-900 mb-6">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-4xl mb-3">👁️</div>
              <h3 className="font-bold text-blue-900 mb-2">See</h3>
              <p className="text-sm text-blue-800">Look at a beautiful image and hear the Spanish word</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">🧠</div>
              <h3 className="font-bold text-blue-900 mb-2">Think</h3>
              <p className="text-sm text-blue-800">Your brain makes the connection (2 seconds)</p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-3">✓</div>
              <h3 className="font-bold text-blue-900 mb-2">Confirm</h3>
              <p className="text-sm text-blue-800">The Spanish word appears to reinforce learning</p>
            </div>
          </div>
        </section>

        <section className="mb-16">
          <h2 className="text-3xl font-bold text-gray-800 mb-8">Featured Lessons</h2>
          {/* ChatSkeleton hidden for now */}
        </section>

        <section className="bg-gradient-to-r from-orange-100 to-orange-50 rounded-2xl p-8 text-center border border-orange-200">
          <h3 className="text-2xl font-bold text-orange-900 mb-3">Ready to start learning?</h3>
          <p className="text-orange-800 mb-6">No sign-up required. Jump into your first lesson now.</p>
          <Link
            to="/day-two"
            className="inline-block px-8 py-3 bg-orange-500 text-white font-bold rounded-xl hover:bg-orange-600 transition-colors"
          >
            Start Learning Now →
          </Link>
        </section>
      </div>
    </div>
  )
}
