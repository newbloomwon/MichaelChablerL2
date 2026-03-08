import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export default function Splash() {
  const [audioUnlocked, setAudioUnlocked] = useState(false);
  const navigate = useNavigate();

  const handleStart = () => {
    // Unlock audio context using a silent Howler sound
    // (Howler.js integration will be added in the next step)
    setAudioUnlocked(true);
    navigate('/home');
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-orange-100 to-orange-300">
      <h1 className="text-5xl font-bold text-orange-700 mb-6">Welcome to LingoVision</h1>
      <p className="text-lg text-gray-700 mb-8 max-w-xl text-center">
        Visual-first Spanish learning. Unlock audio and start your immersive journey!
      </p>
      <button
        onClick={handleStart}
        className="px-10 py-4 bg-orange-500 text-white text-xl font-semibold rounded-2xl shadow-lg hover:bg-orange-600 transition-colors"
      >
        Start Unit
      </button>
      <p className="text-sm text-gray-500 mt-8">(Audio will be unlocked for this session)</p>
    </div>
  );
}
