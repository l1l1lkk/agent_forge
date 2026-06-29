import type { Message } from '../api/client'
import { User, Bot, Wrench } from 'lucide-react'

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const isTool = message.role === 'tool'

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-forge-600' : isTool ? 'bg-yellow-700' : 'bg-gray-700'
      }`}>
        {isUser ? <User size={16} /> : isTool ? <Wrench size={16} /> : <Bot size={16} />}
      </div>
      <div className={`max-w-[80%] rounded-lg p-3 ${
        isUser ? 'bg-forge-600/30 text-gray-100' :
        isTool ? 'bg-yellow-900/20 text-yellow-200' :
        'bg-gray-800/50 text-gray-200'
      }`}>
        <div className="text-xs text-gray-500 mb-1">
          {isUser ? 'You' : isTool ? 'Tool' : 'Assistant'} · #{message.seq}
        </div>
        <div className="text-sm whitespace-pre-wrap break-words">
          {message.content || '(empty)'}
        </div>
      </div>
    </div>
  )
}
