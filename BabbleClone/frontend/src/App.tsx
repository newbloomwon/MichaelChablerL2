import React from 'react'
import { Routes, Route } from 'react-router-dom'

import Home from './pages/Home'
import DayTwo from './pages/DayTwo'
import Splash from './pages/Splash'
import Header from './components/Header'

export default function App() {
  return (
    <div>
      <Header />
      <main className="p-4">
        <Routes>
          <Route path="/" element={<Splash />} />
          <Route path="/home" element={<Home />} />
          <Route path="/day-two" element={<DayTwo />} />
        </Routes>
      </main>
    </div>
  )
}
