import React from 'react'

export default function Header() {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-orange-500 text-white shadow-md">
      <div className="flex items-center gap-2">
        <div className="text-3xl font-bold">+B</div>
        <div>
          <div className="font-bold text-lg">BabbelClone</div>
          <div className="text-xs text-orange-100">Learn Spanish</div>
        </div>
      </div>
      <nav>
        <a href="/" className="hover:text-orange-100 transition-colors font-medium">Home</a>
      </nav>
    </header>
  )
}
