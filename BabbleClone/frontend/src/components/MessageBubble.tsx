import React from 'react'

type Msg = {
  id: string
  author: string
  text: string
  ts: number
}

function initials(name: string) {
  if (!name) return '??'
  const parts = name.split(/\s+/).filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

function colorFromName(name: string) {
  const colors = ['bg-indigo-500','bg-green-500','bg-yellow-500','bg-pink-500','bg-purple-500','bg-rose-500','bg-sky-500']
  let h = 0
  for (let i = 0; i < name.length; i++) h = (h << 5) - h + name.charCodeAt(i)
  const idx = Math.abs(h) % colors.length
  return colors[idx]
}

export default function MessageBubble({ msg }: { msg: Msg }) {
  const isMe = msg.author === 'me' || msg.author === 'Me' || msg.author === 'you'
  const authorLabel = isMe ? 'You' : (msg.author || 'Anon')
  const time = new Date(msg.ts)
  const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  return (
    <div className={`flex items-end ${isMe ? 'justify-end' : 'justify-start'} mb-3` }>
      {!isMe && (
        <div className="flex-shrink-0 mr-3">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white ${colorFromName(msg.author || 'anon')}`}>
            {initials(msg.author || 'A')}
          </div>
        </div>
      )}

      <div className={`max-w-[75%] ${isMe ? 'text-right' : 'text-left'}`}>
        <div className="text-xs text-gray-500 mb-1">{authorLabel} • <span className="text-gray-400">{timeStr}</span></div>
        <div className={`${isMe ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-900'} px-3 py-2 rounded-lg whitespace-pre-wrap`}> 
          {msg.text}
        </div>
      </div>

      {isMe && (
        <div className="flex-shrink-0 ml-3">
          <div className={`w-9 h-9 rounded-full flex items-center justify-center text-white ${colorFromName('you')}`}>
            {initials('You')}
          </div>
        </div>
      )}
    </div>
  )
}
