import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMe, getServers, clearToken, regenerateKey } from '../api'
import CommandBox from '../components/CommandBox'
import { ShieldCheck, LogOut, RefreshCw, Server as ServerIcon, ChevronRight } from 'lucide-react'

function ScoreBadge({ score }) {
  if (score === null || score === undefined) {
    return <span className="text-xs text-slate-400">No scans yet</span>
  }
  const color =
    score >= 80 ? 'bg-green-100 text-green-700' : score >= 50 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'
  return <span className={`text-xs font-semibold px-2 py-1 rounded-full ${color}`}>{score}%</span>
}

export default function Dashboard() {
  const [me, setMe] = useState(null)
  const [servers, setServers] = useState([])
  const [loading, setLoading] = useState(true)
  const [regenerating, setRegenerating] = useState(false)
  const navigate = useNavigate()

  async function loadAll() {
    const [meRes, serversRes] = await Promise.all([getMe(), getServers()])
    setMe(meRes.data)
    setServers(serversRes.data)
  }

  useEffect(() => {
    loadAll().finally(() => setLoading(false))
    // Poll every 15s so a scan that just ran shows up without a manual refresh.
    const interval = setInterval(loadAll, 15000)
    return () => clearInterval(interval)
  }, [])

  function handleLogout() {
    clearToken()
    navigate('/login')
  }

  async function handleRegenerate() {
    if (!confirm('This will invalidate your current install commands. Any device using the old key will stop reporting until you update it. Continue?')) {
      return
    }
    setRegenerating(true)
    try {
      const res = await regenerateKey()
      setMe(res.data)
    } finally {
      setRegenerating(false)
    }
  }

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading...</div>
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-slate-900 rounded-lg p-1.5">
              <ShieldCheck className="text-white" size={18} />
            </div>
            <span className="font-semibold text-slate-900">Security Validation Platform</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-500">Hi, {me.username}</span>
            <button onClick={handleLogout} className="flex items-center gap-1 text-sm text-slate-500 hover:text-slate-900">
              <LogOut size={16} /> Log out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        <section className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-1">Scan a machine</h2>
          <p className="text-sm text-slate-500 mb-5">
            Copy the command for your operating system and run it in a terminal on the machine you want to check.
            Results show up below automatically, usually within a few seconds.
          </p>

          <div className="space-y-5">
            <CommandBox label="Linux / macOS (Terminal)" command={me.install_linux} />
            <CommandBox label="Windows (PowerShell)" command={me.install_windows} />
          </div>

          <button
            onClick={handleRegenerate}
            disabled={regenerating}
            className="mt-5 flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-900 disabled:opacity-60"
          >
            <RefreshCw size={13} className={regenerating ? 'animate-spin' : ''} />
            Regenerate my key (do this if you think it's been shared or leaked)
          </button>
        </section>

        <section className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Your scanned machines</h2>

          {servers.length === 0 ? (
            <div className="text-center py-10 text-slate-400">
              <ServerIcon className="mx-auto mb-2" size={28} />
              <p className="text-sm">No machines scanned yet. Run one of the commands above to get started.</p>
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {servers.map((s) => (
                <li key={s.id}>
                  <button
                    onClick={() => navigate(`/servers/${s.id}`)}
                    className="w-full flex items-center justify-between py-3 text-left hover:bg-slate-50 px-2 -mx-2 rounded-lg"
                  >
                    <div>
                      <p className="text-sm font-medium text-slate-900">{s.hostname}</p>
                      <p className="text-xs text-slate-500">
                        {s.ip_address} - {s.os_type}
                        {s.latest_scanned_at && ` - last scanned ${new Date(s.latest_scanned_at).toLocaleString()}`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <ScoreBadge score={s.latest_score} />
                      <ChevronRight size={16} className="text-slate-400" />
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  )
}
