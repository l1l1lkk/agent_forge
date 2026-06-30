import { useEffect, useState } from 'react'
import { GitBranch, GitCommit, FileWarning, FolderOpen, RefreshCw } from 'lucide-react'
import { useAppStore } from '../../stores/appStore'
import { fetchGitStatus, fetchGitDiff } from '../../api/client'

interface GitStatus {
  in_repo: boolean
  path: string
  repo_root: string
  branch: string | null
  dirty_count: number
  dirty_files: string[]
  recent_commits: Array<{ raw: string }>
  error?: string
}

export function GitWorkspacePanel() {
  const setView = useAppStore((s) => s.setView)
  const [data, setData] = useState<GitStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Diff viewer state
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [diffContent, setDiffContent] = useState<string | null>(null)
  const [diffLoading, setDiffLoading] = useState(false)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const gitData = await fetchGitStatus()
      setData(gitData)
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  async function handleFileClick(file: string) {
    if (!data?.repo_root) return
    setSelectedFile(file)
    setDiffLoading(true)
    setDiffContent(null)
    try {
      const diff = await fetchGitDiff(data.repo_root, file)
      setDiffContent(diff)
    } catch (e) {
      setDiffContent(`Error loading diff: ${e}`)
    } finally {
      setDiffLoading(false)
    }
  }

  function closeDiff() {
    setSelectedFile(null)
    setDiffContent(null)
  }

  function renderDiff(diff: string) {
    const lines = diff.split('\n')
    return (
      <div className="font-mono text-xs leading-relaxed overflow-x-auto">
        {lines.map((line, i) => {
          let cls = 'px-2 py-0'
          if (line.startsWith('+') && !line.startsWith('+++')) {
            cls += ' bg-green-900/30 text-green-300'
          } else if (line.startsWith('-') && !line.startsWith('---')) {
            cls += ' bg-red-900/30 text-red-300'
          } else if (line.startsWith('@@')) {
            cls += ' bg-cyan-900/20 text-cyan-300'
          } else if (line.startsWith('diff ') || line.startsWith('index ') || line.startsWith('---') || line.startsWith('+++')) {
            cls += ' text-app-muted'
          }
          return <div key={i} className={cls}>{line || ' '}</div>
        })}
      </div>
    )
  }

  useEffect(() => { load() }, [])

  return (
    <main className="flex min-w-0 flex-1 flex-col bg-app-bg">
      <div className="flex h-12 items-center justify-between border-b border-app-border px-5">
        <div className="flex items-center gap-2">
          <GitBranch size={16} className="text-app-accent" />
          <h2 className="text-sm font-semibold text-app-text">Git Workspace</h2>
          <span className="rounded bg-app-badge px-1.5 py-0.5 text-[10px] font-bold uppercase text-app-muted">Read-only</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="rounded-lg p-2 text-app-muted hover:bg-app-hover hover:text-app-text"
            onClick={load}
            title="Refresh"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
          <button
            className="rounded-lg border border-app-border px-3 py-1.5 text-sm text-app-secondary hover:bg-app-hover hover:text-app-text"
            onClick={() => setView('workspace')}
          >
            Back to Workspace
          </button>
        </div>
      </div>

      <div className="overflow-y-auto p-5 space-y-4">
        {loading && !data && (
          <div className="text-sm text-app-muted flex items-center gap-2">
            <RefreshCw size={14} className="animate-spin" />
            Loading git workspace status...
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-800 bg-red-900/20 p-4">
            <div className="text-sm font-semibold text-red-400">Error loading git status</div>
            <div className="mt-1 text-sm text-red-300">{error}</div>
            <button
              className="mt-3 rounded-lg border border-red-700 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/40"
              onClick={load}
            >
              Retry
            </button>
          </div>
        )}

        {data && (
          <>
            {data.error && !data.in_repo && (
              <div className="rounded-xl border border-amber-800 bg-amber-900/20 p-4">
                <div className="flex items-center gap-2">
                  <FileWarning size={16} className="text-amber-400" />
                  <span className="text-sm text-amber-300">{data.error}</span>
                </div>
                <div className="mt-2 text-xs text-amber-400/70">
                  Open a project to see git workspace information.
                </div>
              </div>
            )}

            {/* Project Path */}
            <section className="rounded-xl border border-app-border bg-app-panel p-4">
              <div className="flex items-center gap-2 mb-2">
                <FolderOpen size={16} className="text-app-accent" />
                <h3 className="text-sm font-semibold text-app-text">Project Path</h3>
              </div>
              <div className="rounded-lg bg-app-bg px-3 py-2 font-mono text-sm text-app-text break-all">
                {data.path}
              </div>
              {data.repo_root && data.repo_root !== data.path && (
                <div className="mt-2 text-xs text-app-muted">
                  Repo root: <span className="font-mono text-app-secondary">{data.repo_root}</span>
                </div>
              )}
            </section>

            {/* Branch & Dirty Status */}
            {data.in_repo && (
              <section className="rounded-xl border border-app-border bg-app-panel p-4">
                <h3 className="text-sm font-semibold text-app-text mb-3">Status</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="rounded-lg border border-app-border/60 bg-app-bg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <GitBranch size={14} className="text-app-accent" />
                      <span className="text-xs text-app-muted">Current Branch</span>
                    </div>
                    <div className="font-mono text-sm text-app-text">{data.branch}</div>
                  </div>
                  <div className={`rounded-lg border bg-app-bg p-3 ${
                    data.dirty_count > 0 ? 'border-amber-700/50' : 'border-app-border/60'
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <FileWarning size={14} className={data.dirty_count > 0 ? 'text-amber-400' : 'text-green-400'} />
                      <span className="text-xs text-app-muted">Dirty Files</span>
                    </div>
                    <div className={`font-mono text-sm font-bold ${
                      data.dirty_count > 0 ? 'text-amber-400' : 'text-green-400'
                    }`}>
                      {data.dirty_count === 0 ? 'Clean' : `${data.dirty_count} file${data.dirty_count > 1 ? 's' : ''}`}
                    </div>
                  </div>
                </div>

                {/* Dirty file list */}
                {data.dirty_files.length > 0 && (
                  <div className="mt-3 rounded-lg border border-amber-800/40 bg-amber-900/10 p-3 max-h-48 overflow-y-auto">
                    <div className="text-xs text-amber-400/80 font-semibold mb-2">Modified Files</div>
                    {data.dirty_files.map((f, i) => (
                      <button
                        key={i}
                        onClick={() => handleFileClick(f)}
                        className={`w-full text-left font-mono text-xs py-0.5 truncate rounded px-1 -mx-1 transition-colors ${
                          selectedFile === f
                            ? 'bg-app-accent/20 text-app-accent'
                            : 'text-app-secondary hover:bg-app-hover hover:text-app-text'
                        }`}
                      >
                        {f}
                      </button>
                    ))}
                  </div>
                )}

                {/* Diff viewer */}
                {selectedFile && (
                  <div className="mt-3 rounded-lg border border-app-border bg-black/20 p-3 max-h-80 overflow-auto">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-app-accent font-semibold font-mono">
                        Diff: {selectedFile}
                      </span>
                      <button
                        onClick={closeDiff}
                        className="text-xs text-app-muted hover:text-app-text px-1"
                        title="Close diff"
                      >
                        x
                      </button>
                    </div>
                    {diffLoading ? (
                      <div className="text-xs text-app-muted flex items-center gap-2">
                        <RefreshCw size={12} className="animate-spin" />
                        Loading diff...
                      </div>
                    ) : diffContent !== null ? (
                      diffContent.startsWith('Error') ? (
                        <div className="text-xs text-red-400">{diffContent}</div>
                      ) : diffContent === '' ? (
                        <div className="text-xs text-app-muted">No changes (clean file).</div>
                      ) : (
                        renderDiff(diffContent)
                      )
                    ) : null}
                  </div>
                )}
              </section>
            )}

            {/* Recent Commits */}
            {data.in_repo && data.recent_commits.length > 0 && (
              <section className="rounded-xl border border-app-border bg-app-panel p-4">
                <div className="flex items-center gap-2 mb-3">
                  <GitCommit size={16} className="text-app-accent" />
                  <h3 className="text-sm font-semibold text-app-text">Recent Commits</h3>
                </div>
                <div className="space-y-1">
                  {data.recent_commits.map((c, i) => (
                    <div
                      key={i}
                      className={`flex items-center gap-2 rounded-lg px-3 py-2 font-mono text-xs ${
                        i === 0 ? 'bg-app-accent/10 text-app-text' : 'text-app-secondary'
                      }`}
                    >
                      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${
                        i === 0 ? 'bg-app-accent' : 'bg-app-border'
                      }`} />
                      <span className="truncate">{c.raw}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* No-commit empty state */}
            {data.in_repo && data.recent_commits.length === 0 && (
              <section className="rounded-xl border border-app-border bg-app-panel p-4">
                <div className="flex items-center gap-2 mb-3">
                  <GitCommit size={16} className="text-app-muted" />
                  <h3 className="text-sm font-semibold text-app-text">Recent Commits</h3>
                </div>
                <div className="text-xs text-app-muted">No commits yet in this repository.</div>
              </section>
            )}
          </>
        )}
      </div>
    </main>
  )
}
