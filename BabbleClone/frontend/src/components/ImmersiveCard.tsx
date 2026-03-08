
import React, { useState, useEffect } from 'react'
import { LingoCard } from '../types/LingoCard'
import { motion, AnimatePresence } from 'framer-motion'
import { Howl } from 'howler'

interface ImmersiveCardProps {
  card: LingoCard
  onNext: () => void
  onBack: () => void
  cardIndex: number
  totalCards: number
}

export default function ImmersiveCard({
  card,
  onNext,
  onBack,
  cardIndex,
  totalCards,
}: ImmersiveCardProps) {
  const [isTextRevealed, setIsTextRevealed] = useState(false)


  // Timers: play audio immediately, reveal text after 2s

  const [progress, setProgress] = useState(0)

  useEffect(() => {
    let sentenceTimer1: ReturnType<typeof setTimeout> | null = null
    let sentenceTimer2: ReturnType<typeof setTimeout> | null = null
    let revealTimer: ReturnType<typeof setTimeout> | null = null
    setIsTextRevealed(false)
    setProgress(0)
    // Speak the main word first
    playAudio(card.target_text)
    // After 1s, speak the full sentence (first time)
    if (card.sentence) {
      sentenceTimer1 = setTimeout(() => {
        playAudio(card.sentence)
        // After 2s, speak the sentence again
        sentenceTimer2 = setTimeout(() => {
          playAudio(card.sentence)
          // Start progress bar for 3s, then reveal text
          let start = Date.now()
          const duration = 3000
          const update = () => {
            const elapsed = Date.now() - start
            setProgress(Math.min(elapsed / duration, 1))
            if (elapsed < duration) {
              requestAnimationFrame(update)
            }
          }
          update()
          revealTimer = setTimeout(() => {
            setIsTextRevealed(true)
            setProgress(0)
          }, duration)
        }, 2000)
      }, 1000)
    }
    return () => {
      if (sentenceTimer1) clearTimeout(sentenceTimer1)
      if (sentenceTimer2) clearTimeout(sentenceTimer2)
      if (revealTimer) clearTimeout(revealTimer)
    }
  }, [card.id])

  // Play either a word or a sentence
  const playAudio = (text?: string) => {
    if (card.audio_url && !text) {
      const sound = new Howl({ src: [card.audio_url] })
      sound.play()
    } else if (text) {
      // If text is provided, use SpeechSynthesis
      const utterance = new SpeechSynthesisUtterance(text)
      utterance.lang = 'es-ES'
      utterance.rate = 0.95
      speechSynthesis.speak(utterance)
    }
  }


  const handleReplayAudio = () => {
    playAudio(card.target_text)
    if (card.sentence) {
      setTimeout(() => {
        playAudio(card.sentence)
        setTimeout(() => playAudio(card.sentence), 2000)
      }, 1000)
    }
    setIsTextRevealed(false)
    setTimeout(() => setIsTextRevealed(true), 6000)
  }

  const mainImageSrc = card.visual_url

  return (
    <div className="flex flex-col items-center justify-center gap-6 w-full max-w-2xl mx-auto px-4">
      {/* Progress indicator */}
      <div className="w-full bg-gray-200 rounded-full h-1">
        <div
          className="bg-orange-500 h-1 rounded-full transition-all duration-300"
          style={{ width: `${((cardIndex + 1) / totalCards) * 100}%` }}
        ></div>
      </div>

      {/* Image section with rounded corners */}
      <div className="relative w-full h-96 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl overflow-hidden shadow-sm">
        <img
          src={mainImageSrc}
          alt={card.english_bridge || card.target_text}
          className="w-full h-full object-contain p-8"
          onError={(e) => {
            e.currentTarget.src =
              'https://via.placeholder.com/400x300?text=Image+Not+Available'
          }}
        />
      </div>

      {/* Audio replay button - Babbel style */}
      <button
        onClick={handleReplayAudio}
        className="px-8 py-3 bg-orange-500 text-white font-semibold rounded-xl hover:bg-orange-600 transition-colors shadow-md"
      >
        🔊 Hear Again
      </button>

      {/* Text reveal section */}
      <div className="text-center min-h-32 flex items-center justify-center w-full">
        {!isTextRevealed && (
          <div className="text-center">
            <p className="text-gray-500 text-lg font-medium mb-3">Listen and think...</p>
            <div className="flex gap-2 justify-center">
              <div className="w-3 h-3 bg-orange-400 rounded-full animate-bounce"></div>
              <div className="w-3 h-3 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-3 h-3 bg-orange-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        )}
        
        {/* Progress bar during thinking gap */}
        {!isTextRevealed && progress > 0 && progress < 1 && (
          <div className="w-full max-w-md h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
            <div
              className="h-2 bg-orange-400 transition-all duration-100"
              style={{ width: `${progress * 100}%` }}
            ></div>
          </div>
        )}
        <AnimatePresence>
          {isTextRevealed && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 20 }}
              transition={{ duration: 0.7 }}
              className="w-full"
            >
              <p className="text-5xl font-bold text-orange-600 mb-2">{card.target_text}</p>
              {card.sentence && (
                <p className="text-gray-700 text-lg mt-2 italic">{card.sentence}</p>
              )}
              {card.grammar_note && (
                <p className="text-gray-700 text-lg mt-2 italic">{card.grammar_note}</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation buttons - Babbel style */}
      <div className="flex gap-3 w-full justify-between">
        <button
          onClick={onBack}
          disabled={cardIndex === 0}
          className="flex-1 px-4 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          ← Back
        </button>
        <button
          onClick={onNext}
          disabled={cardIndex === totalCards - 1}
          className="flex-1 px-4 py-3 bg-orange-500 text-white font-semibold rounded-xl hover:bg-orange-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          Next →
        </button>
      </div>

      {/* Card counter */}
      <p className="text-gray-500 text-sm font-medium">
        {cardIndex + 1} / {totalCards}
      </p>
    </div>
  )
}
