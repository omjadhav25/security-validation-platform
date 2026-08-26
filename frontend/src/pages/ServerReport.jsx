import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { getReport, downloadPdfReport } from '../api'
import { ArrowLeft, Download, CheckCircle2, XCircle } from 'lucide-react'

const SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-blue-100 text-blue-700',
}

function ScoreRing({ score }) {
  const color = score >= 80 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626'
  return (
    <div className="flex flex-col items-center">
      <div
        className="w-24 h-24 rounded-full flex items-center justify-center text-xl font-bold"
        style={{ background: `conic-gradient(${color} ${score * 3.6}deg, #e2e8f0 0deg)` }}
      >
        <div className="w-[72px] h-[72px] rounded-full bg-white flex items-center justify-center" style={{ color }}>
          {score}%
        </div>
      </div>
      <p className="text-xs text-slate-500 mt-2">Compliance score</p>
    </div>
  )
}

export default function ServerReport() {
  const { serverId } = useParams()
  const navigate = useNavigate()
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState(false)

  useEffect(() => {
    getReport(serverId)
      .then((res) => setReport(res.data))
      .catch(() => setError('Could not load this report.'))
  }, [serverId])

  async function handleDownload() {
    setDownloading(true)
    try {
      await downloadPdfReport(serverId, report.server.hostname)
    } finally {
      setDownloading(false)
    }
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-3 text-slate-500">
        <p>{error}</p>
        <Link to="/" className="text-slate-900 underline text-sm">Back to dashboard</Link>
      </div>
    )
  }

  if (!report) {
    return <div className="min-h-screen flex items-center justify-center text-slate-500">Loading...</div>
  }

  const { server, latest_scan: scan } = report
  const sorted = [...scan.findings].sort((a, b) => {
    const order = { critical: 0, medium: 1, low: 2 }
    return (order[a.severity] ?? 3) - (order[b.severity] ?? 3)
  })

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <button onClick={() => navigate('/')} className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900">
            <ArrowLeft size={16} /> Back to dashboard
          </button>
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="flex items-center gap-1.5 text-sm bg-slate-900 text-white px-3 py-1.5 rounded-lg hover:bg-slate-800 disabled:opacity-60"
          >
            <Download size={15} /> {downloading ? 'Preparing...' : 'Download PDF'}
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-6">
        <section className="bg-white rounded-2xl border border-slate-200 p-6 flex items-center justify-between flex-wrap gap-6">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{server.hostname}</h1>
            <p className="text-sm text-slate-500 mt-1">{server.ip_address} - {server.os_type}</p>
            <p className="text-xs text-slate-400 mt-1">Scanned {new Date(scan.scanned_at).toLocaleString()}</p>
          </div>
          <ScoreRing score={scan.score} />
        </section>

        <section className="bg-white rounded-2xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Findings</h2>
          <ul className="divide-y divide-slate-100">
            {sorted.map((f, i) => (
              <li key={i} className="py-3 flex items-start gap-3">
                {f.passed ? (
                  <CheckCircle2 className="text-green-600 mt-0.5 shrink-0" size={18} />
                ) : (
                  <XCircle className="text-red-500 mt-0.5 shrink-0" size={18} />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-medium text-slate-900">{f.title}</span>
                    <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full ${SEVERITY_STYLES[f.severity] || 'bg-slate-100 text-slate-600'}`}>
                      {f.severity}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">{f.control_id}</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{f.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  )
}
