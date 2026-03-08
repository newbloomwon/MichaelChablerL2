import React, { useState } from 'react'

import { useLessonStore } from '../store/lessonStore'
import { LingoCard } from '../types/LingoCard'
import ImmersiveCard from '../components/ImmersiveCard'

// Fetch lesson cards from mock API (local JSON file)

export default function DayTwo() {
  const { cards, currentIndex, setCards, nextCard, prevCard } = useLessonStore()

  React.useEffect(() => {
    fetch('/src/mocks/lessonCards.json')
      .then((res) => res.json())
      .then((data: LingoCard[]) => setCards(data))
      .catch(() => setCards([]))
  }, [setCards])

  if (!cards.length) return <div className="text-center p-8">Loading...</div>

  return (
    <div className="flex flex-col items-center justify-center min-h-screen">
      <ImmersiveCard
        card={cards[currentIndex]}
        onNext={nextCard}
        onBack={prevCard}
        cardIndex={currentIndex}
        totalCards={cards.length}
      />
    </div>
  )

  const currentCard = LESSON_DATA[currentCardIndex]

  const handleStartLesson = () => {
    setLessonStarted(true)
  }

  const handleNext = () => {
    if (currentCardIndex === LESSON_DATA.length - 1) {
      setLessonCompleted(true)
    } else {
      setCurrentCardIndex(currentCardIndex + 1)
    }
  }

  const handleBack = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(currentCardIndex - 1)
    }
  }

  const handleRestartLesson = () => {
    setCurrentCardIndex(0)
    setLessonStarted(false)
    setLessonCompleted(false)
  }

  if (lessonCompleted) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="text-center space-y-8">
          <div className="text-7xl">🎉</div>
          <h1 className="text-5xl font-bold text-orange-600">
            ¡Felicitaciones!
          </h1>
          <p className="text-xl text-gray-700 max-w-xl mx-auto">
            You've completed the lesson! You've learned 10 Spanish words through visual-first immersion.
          </p>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 p-8 rounded-2xl border border-orange-200">
            <p className="text-lg font-semibold text-orange-900 mb-6">
              Vocabulary Mastered:
            </p>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {LESSON_DATA.map((card) => (
                <div key={card.id} className="bg-white p-4 rounded-xl shadow-sm">
                  <p className="font-bold text-orange-600 text-lg">{card.spanish}</p>
                  <p className="text-xs text-gray-500 mt-1">{card.english}</p>
                </div>
              ))}
            </div>
          </div>

          <p className="text-gray-600 text-lg">
            Ready for the next lesson?
          </p>

          <button
            onClick={handleRestartLesson}
            className="px-10 py-4 bg-orange-500 text-white font-bold rounded-xl hover:bg-orange-600 transition-colors text-lg shadow-md"
          >
            Review Lesson Again
          </button>
        </div>
      </div>
    )
  }

  if (!lessonStarted) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="text-center space-y-10">
          <h1 className="text-5xl font-bold text-gray-800">Vocabulary Lesson</h1>
          <p className="text-xl text-gray-600">Learning Spanish through Images</p>

          <div className="bg-gradient-to-br from-orange-50 to-white p-10 rounded-2xl border border-orange-200">
            <p className="text-lg text-gray-800 mb-8 font-medium">
              Here's how this lesson works:
            </p>

            <div className="space-y-6 text-left max-w-2xl mx-auto">
              <div className="flex items-start gap-4">
                <span className="text-4xl">1️⃣</span>
                <div>
                  <p className="font-bold text-lg text-gray-800">See the Image</p>
                  <p className="text-gray-600 mt-1">
                    Look at a picture and hear the Spanish word
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <span className="text-4xl">2️⃣</span>
                <div>
                  <p className="font-bold text-lg text-gray-800">Think (2 seconds)</p>
                  <p className="text-gray-600 mt-1">
                    Your brain connects the image and sound
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-4">
                <span className="text-4xl">3️⃣</span>
                <div>
                  <p className="font-bold text-lg text-gray-800">See the Word</p>
                  <p className="text-gray-600 mt-1">
                    The Spanish word appears to confirm your thinking
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-10 p-6 bg-blue-50 rounded-xl border border-blue-200">
              <p className="text-sm text-blue-900 font-medium">
                💡 No Translations: You learn to think in Spanish, not translate from English
              </p>
            </div>
          </div>

          <p className="text-gray-600 text-lg max-w-xl mx-auto">
            You'll learn 10 common Spanish words. Take your time and let your brain make the visual associations!
          </p>

          <button
            onClick={handleStartLesson}
            className="px-12 py-4 bg-orange-500 text-white text-lg font-bold rounded-xl hover:bg-orange-600 transition-colors shadow-lg"
          >
            Start Learning →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-white to-gray-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <ImmersiveCard
          card={currentCard}
          onNext={handleNext}
          onBack={handleBack}
          cardIndex={currentCardIndex}
          totalCards={LESSON_DATA.length}
        />
      </div>
    </div>
  )
}
