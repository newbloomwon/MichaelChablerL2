import React, { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble'
import useWebSocket from '../hooks/useWebSocket'

type Msg = {
  id: string
  author: 'me' | 'bot' | string
  text: string
  ts: number
}

const BACKEND_HTTP = import.meta.env.VITE_BACKEND_HTTP || 'http://localhost:3000'
const BACKEND_WS = import.meta.env.VITE_BACKEND_WS || 'ws://localhost:3000/ws'

export default function ChatSkeleton() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [text, setText] = useState('')
  const listRef = useRef<HTMLDivElement | null>(null)

  // handle incoming WS messages
  const { send, status } = useWebSocket(BACKEND_WS, (data: any) => {
    if (data && data.id) setMessages(prev => [...prev, data])
  })

  useEffect(() => {
    // fetch history on mount
    fetch(`${BACKEND_HTTP}/messages`).then(r => r.json()).then((msgs: Msg[]) => {
      setMessages(msgs || [])
    }).catch(() => {})
  }, [])

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
    }
  }, [messages])

  function handleSend(e?: React.FormEvent) {
    e?.preventDefault()
    const trimmed = text.trim()
    if (!trimmed) return

    const payload = { author: 'me', text: trimmed }
    try { send(payload) } catch (e) { console.error('ws send failed', e) }
    setText('')
  }

  return (
    <div className="border border-gray-200 rounded-lg p-3">
      <div className="mb-2 text-sm text-gray-500">WS: {status}</div>
      <div ref={listRef} className="h-80 overflow-auto bg-gray-50 rounded-md p-3">
        {messages.length === 0 ? (
          <p className="text-gray-500">No messages yet — say hello 👋</p>
        ) : (
          messages.map(m => <MessageBubble key={m.id} msg={m} />)
        )}
      </div>

      <form onSubmit={handleSend} className="flex gap-2 mt-3">
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 px-3 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-indigo-200"
        />
        <button type="submit" className="px-3 py-2 rounded-md bg-indigo-600 text-white hover:bg-indigo-700">Send</button>
      </form>
    </div>
  )
}
