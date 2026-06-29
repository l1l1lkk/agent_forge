export function EmptyWorkspace() {
  return (
    <main className="flex min-w-0 flex-1 items-center justify-center bg-app-bg">
      <div className="max-w-md text-center">
        <div className="mb-4 text-5xl">🌀</div>
        <h1 className="text-2xl font-semibold text-app-text">Select a session</h1>
        <p className="mt-2 text-sm leading-6 text-app-muted">Choose an agent session from the sidebar, or create a new one to start working with Agent Forge.</p>
      </div>
    </main>
  )
}
