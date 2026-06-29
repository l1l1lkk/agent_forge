import { useState } from 'react'
import { ArrowUp, Paperclip, Square } from 'lucide-react'
import { useSessionStore } from '../../stores/sessionStore'
import { useMessageStore } from '../../stores/messageStore'

export function Composer() {
  const [value, setValue] = useState('')
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId)
  const appendUserMessage = useMessageStore((s) => s.appendUserMessage)
  const runningBySession = useMessageStore((s) => s.runningBySession)
  const isRunning = selectedSessionId ? (runningBySession[selectedSessionId] ?? false) : false

  function send() {
    const content = value.trim()
    if (!content || !selectedSessionId) return
    appendUserMessage(selectedSessionId, content)
    setValue('')
  }

  return (
    <div className="border-t border-app-border bg-app-bg px-5 py-4">
      <div className="mx-auto max-w-3xl">
        <div className="rounded-2xl border border-app-border bg-app-panel shadow-lg shadow-black/20 focus-within:border-app-accent/60 transition-colors">
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
            }}
            placeholder={isRunning ? 'Send to queue, or press Esc to interrupt...' : 'Send a message...'}
            className="min-h-[72px] w-full resize-none bg-transparent px-4 pt-4 pb-1 text-sm leading-6 text-app-text outline-none placeholder:text-app-muted"
          />
          <div className="flex items-center justify-between px-3 pb-3">
            <button className="rounded-lg p-2 text-app-muted hover:bg-app-hover hover:text-app-text">
              <Paperclip size={17} />
            </button>
            {isRunning ? (
              <button className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500 text-white hover:bg-red-400">
                <Square size={15} />
              </button>
            ) : (
              <button onClick={send} disabled={!value.trim()} className="flex h-9 w-9 items-center justify-center rounded-xl bg-app-accent text-white hover:bg-violet-600 disabled:cursor-not-allowed disabled:opacity-40 transition-colors">
                <ArrowUp size={17} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
