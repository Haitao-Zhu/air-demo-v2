import { useState, useEffect, useRef, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

interface Message {
  id: string
  role: string
  content: string
  isUser: boolean
  timestamp: number
}

type ConnectionStatus = 'connecting' | 'connected' | 'disconnected'

function generateId() {
  return Math.random().toString(36).substring(2, 15)
}

function getAgentColor(role: string): string {
  const colors = [
    '#6c5ce7', '#00b894', '#0984e3', '#e17055',
    '#fdcb6e', '#e84393', '#00cec9', '#636e72',
  ]
  let hash = 0
  for (let i = 0; i < role.length; i++) {
    hash = role.charCodeAt(i) + ((hash << 5) - hash)
  }
  return colors[Math.abs(hash) % colors.length]
}

function getInitials(role: string): string {
  return role
    .split(/[\s_-]+/)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2)
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [status, setStatus] = useState<ConnectionStatus>('connecting')
  const [isWaiting, setIsWaiting] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/test_user`
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => setStatus('connected')
    ws.onclose = () => {
      setStatus('disconnected')
      setIsWaiting(false)
    }
    ws.onerror = () => {
      setStatus('disconnected')
      setIsWaiting(false)
    }

    ws.onmessage = (event) => {
      const data = event.data as string
      const startIdx = data.indexOf('JSONSTART')
      const endIdx = data.indexOf('JSONEND')
      if (startIdx === -1 || endIdx === -1) return

      const jsonStr = data.substring(startIdx + 9, endIdx)
      try {
        const parsed = JSON.parse(jsonStr)
        const msg: Message = {
          id: generateId(),
          role: parsed.role,
          content: parsed.content,
          isUser: false,
          timestamp: Date.now(),
        }
        setMessages((prev) => [...prev, msg])
        setIsWaiting(false)
      } catch {
        console.error('Failed to parse message')
      }
    }

    return () => {
      ws.close()
    }
  }, [])

  const sendMessage = () => {
    const trimmed = input.trim()
    if (!trimmed || !wsRef.current || status !== 'connected') return

    const userMsg: Message = {
      id: generateId(),
      role: 'You',
      content: trimmed,
      isUser: true,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setIsWaiting(true)

    wsRef.current.send(
      JSON.stringify({ content: trimmed, timestamp: Math.floor(Date.now() / 1000) })
    )

    inputRef.current?.focus()
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <div className="logo-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
            </div>
            <span className="logo-text">AI Refinery &mdash; Flow Demo</span>
          </div>
          <div className={`status-badge status-${status}`}>
            <span className="status-dot" />
            {status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting...' : 'Disconnected'}
          </div>
        </div>
      </header>

      <main className="chat-area">
        {messages.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h2>Intelligent Support Router</h2>
            <p>FlowSuperAgent triage routing demo. Classifies your request and routes it to the right specialist agent — technical support, billing, or both.</p>
            <div className="example-queries">
              <p style={{fontSize: '13px', marginTop: '16px', color: '#9ca3af'}}>Try:</p>
              <p style={{fontSize: '13px', color: '#6b7280'}}>"I'm having a technical issue with my account, can you help?"</p>
              <p style={{fontSize: '13px', color: '#6b7280'}}>"I was double-charged on my last invoice"</p>
              <p style={{fontSize: '13px', color: '#6b7280'}}>"My app keeps crashing and I also need a refund"</p>
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((msg) => (
              <div key={msg.id} className={`message-row ${msg.isUser ? 'user' : 'agent'}`}>
                {!msg.isUser && (
                  <div
                    className="avatar"
                    style={{ backgroundColor: getAgentColor(msg.role) }}
                  >
                    {getInitials(msg.role)}
                  </div>
                )}
                <div className="message-content">
                  {!msg.isUser && <div className="message-role">{msg.role}</div>}
                  <div className={`message-bubble ${msg.isUser ? 'user-bubble' : 'agent-bubble'}`}>
                    {msg.isUser ? (
                      <p>{msg.content}</p>
                    ) : (
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {isWaiting && (
              <div className="message-row agent">
                <div className="avatar" style={{ backgroundColor: '#9ca3af' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                  </svg>
                </div>
                <div className="message-content">
                  <div className="message-bubble agent-bubble">
                    <div className="typing-indicator">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      <footer className="input-area">
        <div className="input-container">
          <textarea
            ref={inputRef}
            className="message-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            rows={1}
            disabled={status !== 'connected'}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={!input.trim() || status !== 'connected'}
            aria-label="Send message"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p className="input-hint">Press Enter to send, Shift+Enter for new line</p>
      </footer>
    </div>
  )
}
