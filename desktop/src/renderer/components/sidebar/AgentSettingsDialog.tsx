import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Plus, X } from 'lucide-react'
import type { Agent, Connector } from '../../api/types'
import { archiveAgent, createAgent, fetchConnectors, updateAgent } from '../../api/client'
import { useAgentStore } from '../../stores/agentStore'

type Props = {
  open: boolean
  initialAgentId: string | null
  onClose: () => void
}

const BUILTIN_TOOLS = ['ask', 'bg'] as const
const ICONS = ['🐙', '🤖', '🧠', '🔬', '🛠️', '✍️', '📊', '🦉'] as const

export function AgentSettingsDialog({ open, initialAgentId, onClose }: Props) {
  const agents = useAgentStore((s) => s.agents)
  const loadAgents = useAgentStore((s) => s.loadAgents)
  const upsertAgent = useAgentStore((s) => s.upsertAgent)
  const [selectedId, setSelectedId] = useState<string | null>(initialAgentId)
  const selected = useMemo(() => agents.find((a) => a.id === selectedId) ?? null, [agents, selectedId])

  const [name, setName] = useState('')
  const [avatar, setAvatar] = useState('🐙')
  const [description, setDescription] = useState('')
  const [systemPrompt, setSystemPrompt] = useState('')
  const [model, setModel] = useState('')
  const [runner, setRunner] = useState('claude')
  const [mcpServers, setMcpServers] = useState<string[]>([...BUILTIN_TOOLS])
  const [toolAllow, setToolAllow] = useState('')
  const [toolDeny, setToolDeny] = useState('')
  const [connectors, setConnectors] = useState<Connector[]>([])
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setSelectedId(initialAgentId)
    fetchConnectors().then(setConnectors).catch(() => setConnectors([]))
  }, [open, initialAgentId])

  useEffect(() => {
    if (!open) return
    setError(null)
    setName(selected?.name ?? '')
    setAvatar(selected?.avatar ?? '🐙')
    setDescription(selected?.description ?? '')
    setSystemPrompt(selected?.systemPrompt ?? '')
    setModel(selected?.model ?? '')
    setRunner(selected?.runner ?? 'claude')
    setMcpServers(selected?.mcpServers?.length ? selected.mcpServers : [...BUILTIN_TOOLS])
    setToolAllow(selected?.toolAllow ?? '')
    setToolDeny(selected?.toolDeny ?? '')
  }, [open, selected])

  if (!open) return null

  const toggleTool = (tool: string) => {
    setMcpServers((cur) => cur.includes(tool) ? cur.filter((x) => x !== tool) : [...cur, tool])
  }

  const save = async () => {
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    setSaving(true)
    setError(null)
    try {
      const payload = {
        name: name.trim(),
        description,
        avatar,
        systemPrompt,
        model,
        runner,
        mcpServers,
        toolAllow,
        toolDeny,
      }
      const saved = selected ? await updateAgent(selected.id, payload) : await createAgent(payload)
      upsertAgent(saved)
      await loadAgents()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  const archive = async () => {
    if (!selected) return
    setSaving(true)
    setError(null)
    try {
      await archiveAgent(selected.id)
      await loadAgents()
      onClose()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 px-4" onMouseDown={onClose}>
      <div
        className="agent-settings-dialog flex max-h-[92vh] w-full max-w-3xl flex-col rounded-xl border border-app-border bg-app-panel shadow-2xl"
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 px-6 pt-5">
          <div>
            <h2 className="text-lg font-semibold text-app-text">Agent settings</h2>
            <p className="mt-1 max-w-2xl text-sm leading-6 text-app-muted">
              An agent is a durable assistant: its system prompt, model, tools and schedules persist across sessions. Pick one to edit, or create a new one.
            </p>
          </div>
          <button className="rounded-lg p-1.5 text-app-muted hover:bg-app-hover hover:text-app-text" onClick={onClose} title="Close">
            <X size={18} />
          </button>
        </div>

        <div className="grid min-h-0 flex-1 grid-cols-[180px_minmax(0,1fr)] gap-4 overflow-hidden px-6 py-4">
          <div className="space-y-1 overflow-y-auto border-r border-app-border pr-3">
            <button
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm ${selectedId === null ? 'bg-app-selected text-app-text' : 'text-app-secondary hover:bg-app-hover hover:text-app-text'}`}
              onClick={() => setSelectedId(null)}
            >
              <Plus size={15} />
              <span>New agent</span>
            </button>
            {agents.map((agent) => (
              <button
                key={agent.id}
                className={`flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-sm ${selectedId === agent.id ? 'bg-app-selected text-app-text font-medium' : 'text-app-secondary hover:bg-app-hover hover:text-app-text'}`}
                onClick={() => setSelectedId(agent.id)}
                title={agent.name}
              >
                <span className="shrink-0 text-base">{agent.avatar || '🐙'}</span>
                <span className="min-w-0 truncate">{agent.name}</span>
              </button>
            ))}
          </div>

          <div className="min-w-0 space-y-3 overflow-y-auto pr-1">
            <Field label="Name">
              <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Researcher" autoFocus />
            </Field>

            <Field label="Icon">
              <div className="flex flex-wrap items-center gap-1.5">
                {ICONS.map((icon) => (
                  <button
                    key={icon}
                    className={`flex h-9 w-9 items-center justify-center rounded-md border text-lg ${avatar === icon ? 'border-blue-500 bg-blue-500/10' : 'border-app-border hover:bg-app-hover'}`}
                    onClick={() => setAvatar(icon)}
                    aria-pressed={avatar === icon}
                  >
                    {icon}
                  </button>
                ))}
                <input className="input h-9 w-14 text-center" value={avatar} onChange={(e) => setAvatar(e.target.value)} aria-label="Custom icon" />
              </div>
            </Field>

            <Field label="Description">
              <input className="input" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="What this agent is for (optional)" />
            </Field>

            <Field label="System prompt">
              <textarea className="input min-h-[96px] resize-none" value={systemPrompt} onChange={(e) => setSystemPrompt(e.target.value)} placeholder="You are a meticulous research assistant..." />
            </Field>

            <Field label="Model">
              <input className="input" value={model} onChange={(e) => setModel(e.target.value)} placeholder="claude-opus-4-7 (blank = backend default)" />
            </Field>

            <Field label="Harness">
              <div className="grid grid-cols-2 gap-2">
                <HarnessButton label="Claude Code" active={runner === 'claude'} onClick={() => setRunner('claude')} />
                <HarnessButton label="Codex" active={runner === 'codex'} onClick={() => setRunner('codex')} />
              </div>
            </Field>

            <Field label="Built-in tools">
              <div className="flex gap-3 text-sm text-app-text">
                {BUILTIN_TOOLS.map((tool) => (
                  <label key={tool} className="flex items-center gap-1.5">
                    <input type="checkbox" checked={mcpServers.includes(tool)} onChange={() => toggleTool(tool)} />
                    {tool}
                  </label>
                ))}
              </div>
            </Field>

            <Field label="Connectors">
              {connectors.length === 0 ? (
                <p className="text-xs text-app-muted">No connectors installed yet - add one in the sidebar's Connectors section.</p>
              ) : (
                <div className="space-y-1 text-sm text-app-secondary">
                  {connectors.map((connector) => (
                    <label key={connector.id} className="flex items-center gap-2">
                      <input type="checkbox" disabled />
                      <span>{connector.label}</span>
                      <span className="text-xs text-app-muted">{connector.status}</span>
                    </label>
                  ))}
                </div>
              )}
            </Field>

            <div className="grid grid-cols-2 gap-2">
              <Field label="Allow tools">
                <textarea className="input min-h-[78px] resize-none" value={toolAllow} onChange={(e) => setToolAllow(e.target.value)} placeholder="one per line; blank = all" />
              </Field>
              <Field label="Deny tools">
                <textarea className="input min-h-[78px] resize-none" value={toolDeny} onChange={(e) => setToolDeny(e.target.value)} placeholder="one per line; wins over allow" />
              </Field>
            </div>

            {error && <div className="rounded-lg border border-red-500/30 bg-red-950/30 px-3 py-2 text-sm text-red-200">{error}</div>}
          </div>
        </div>

        <div className="flex items-center justify-between px-6 pb-5">
          {selected ? (
            <button className="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-500 disabled:opacity-50" onClick={archive} disabled={saving}>
              Archive agent
            </button>
          ) : <span />}
          <button className="rounded-lg bg-blue-700 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-600 disabled:opacity-50" onClick={save} disabled={saving}>
            {saving ? 'Saving...' : selected ? 'Save' : 'Create agent'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-app-text">{label}</span>
      {children}
    </label>
  )
}

function HarnessButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      className={`h-9 rounded-lg border text-sm ${active ? 'border-blue-500 bg-blue-500/10 text-app-text' : 'border-app-border text-app-secondary hover:bg-app-hover hover:text-app-text'}`}
      onClick={onClick}
    >
      {label}
    </button>
  )
}
