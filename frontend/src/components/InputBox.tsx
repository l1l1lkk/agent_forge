import { useState, useRef, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'

export function InputBox({ onSend, disabled }: { onSend: (text: string) => void; disabled: boolean }) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = () => {
    const text = input.trim()
    if (!text || disabled) return
    onSend(text)
    setInput('')
    textareaRef.current?.focus()
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex gap-2 items-end">
      <textarea
        ref={textareaRef}
        value={input}
        onChange={e => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? 'Agent is working...' : 'Ask the agent to read, modify, or run code...'}
        rows={2}
        disabled={disabled}
        className="flex-1 bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-100 placeholder-gray-500
                   resize-none focus:outline-none focus:border-forge-500 disabled:opacity-50"
      />
      <button
        onClick={handleSend}
        disabled={disabled || !input.trim()}
        className="px-4 py-3 rounded-lg bg-forge-600 hover:bg-forge-500 disabled:bg-gray-700 disabled:text-gray-500
                   text-white flex items-center gap-1 transition-colors"
      >
        <Send size={16} />
        <span className="text-sm font-medium">Send</span>
      </button>
    </div>
  )
}
