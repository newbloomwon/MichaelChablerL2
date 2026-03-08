import { create } from 'zustand';
import { LingoCard } from '../types/LingoCard';

interface LessonState {
  cards: LingoCard[];
  currentIndex: number;
  isDecoded: boolean;
  setCards: (cards: LingoCard[]) => void;
  nextCard: () => void;
  prevCard: () => void;
  setDecoded: (decoded: boolean) => void;
}

export const useLessonStore = create<LessonState>((set) => ({
  cards: [],
  currentIndex: 0,
  isDecoded: false,
  setCards: (cards) => set({ cards, currentIndex: 0, isDecoded: false }),
  nextCard: () => set((state) => ({
    currentIndex: Math.min(state.currentIndex + 1, state.cards.length - 1),
    isDecoded: false,
  })),
  prevCard: () => set((state) => ({
    currentIndex: Math.max(state.currentIndex - 1, 0),
    isDecoded: false,
  })),
  setDecoded: (decoded) => set({ isDecoded: decoded }),
}));
