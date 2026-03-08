import { useEffect, useRef, useState } from 'react'

type WSStatus = 'connecting' | 'open' | 'closed' | 'error'

export default function useWebSocket(url: string, onMessage: (data: any) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const retriesRef = useRef(0)
  const shouldReconnectRef = useRef(true)
  const sendQueueRef = useRef<any[]>([])
  const [status, setStatus] = useState<WSStatus>('closed')

  useEffect(() => {
    shouldReconnectRef.current = true

    let mounted = true

    function connect() {
      if (!mounted) return
      setStatus('connecting')
      try {
        const ws = new WebSocket(url)
        wsRef.current = ws

        ws.addEventListener('open', () => {
          retriesRef.current = 0
          setStatus('open')
          // flush queue
          while (sendQueueRef.current.length > 0) {
            const item = sendQueueRef.current.shift()
            try { ws.send(typeof item === 'string' ? item : JSON.stringify(item)) } catch {}
          }
        })

        ws.addEventListener('message', (ev) => {
          try {
            const parsed = JSON.parse(ev.data)
            onMessage(parsed)
          } catch (e) {
            // non-json messages
            try { onMessage(ev.data) } catch {}
          }
        })

        ws.addEventListener('close', () => {
          setStatus('closed')
          wsRef.current = null
          if (shouldReconnectRef.current) scheduleReconnect()
        })

        ws.addEventListener('error', () => {
          setStatus('error')
          // close will trigger reconnect
          try { ws.close() } catch {}
        })
      } catch (e) {
        setStatus('error')
        scheduleReconnect()
      }
    }

    function scheduleReconnect() {
      retriesRef.current = Math.min(retriesRef.current + 1, 50)
      const base = 500
      const max = 30000
      const backoff = Math.min(max, Math.floor(base * Math.pow(1.5, retriesRef.current)))
      const jitter = Math.floor(Math.random() * 300)
      const delay = Math.min(max, backoff + jitter)
      setTimeout(() => {
        if (shouldReconnectRef.current) connect()
      }, delay)
    }

    connect()

    return () => {
      mounted = false
      shouldReconnectRef.current = false
      try { wsRef.current?.close() } catch {}
      wsRef.current = null
    }
  }, [url, onMessage])

  function send(payload: any) {
    try {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(typeof payload === 'string' ? payload : JSON.stringify(payload))
      } else {
        // queue for when connection opens
        sendQueueRef.current.push(payload)
      }
    } catch (e) {
      // queue on error
      sendQueueRef.current.push(payload)
    }
  }

  function close() {
    shouldReconnectRef.current = false
    try { wsRef.current?.close() } catch {}
  }

  return { send, close, status }
}
