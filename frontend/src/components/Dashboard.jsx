import { useEffect, useState } from 'react'
import { getServers, getReport } from '../api'
import ScoreGauge from './ScoreGauge'
import FindingsTable from './FindingsTable'
import { Shield, Server, AlertTriangle, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const [servers, setServers] = useState([])
  const [selectedServer, setSelectedServer] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    getServers().then(res => {
      setServers(res.data)
      if (res.data.length > 0) {
        loadReport(res.data[0].id)
      }
    })
  }, [])

  const loadReport = (serverId) => {
    setLoading(true)
    setSelectedServer(serverId)
    getReport(serverId).then(res => {
      setReport(res.data)
      setLoading(false)
    })
  }

  const criticalCount = report?.latest_scan?.findings?.filter(
    f => f.severity === 'critical' && !f.passed
  ).length || 0

  const passedCount = report?.latest_scan?.findings?.filter(
    f => f.passed
  ).length || 0

  const totalCount = report?.latest_scan?.findings?.length || 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3">
          <Shield className="text-blue-600" size={28} />
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              Security Validation Platform
            </h1>
            <p className="text-sm text-gray-500">CIS Benchmark Compliance Scanner</p>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* Sidebar - Server List */}
        <div className="w-64 min-h-screen bg-white border-r border-gray-200 p-4">
          <h2 className="text-xs font-semibold text-gray-500 uppercase mb-3">
            Monitored Servers
          </h2>
          {servers.map(server => (
            <button
              key={server.id}
              onClick={() => loadReport(server.id)}
              className={`w-full text-left px-3 py-3 rounded-lg mb-2 transition-colors ${
                selectedServer === server.id
                  ? 'bg-blue-50 border border-blue-200'
                  : 'hover:bg-gray-50 border border-transparent'
              }`}
            >
              <div className="flex items-center gap-2">
                <Server size={16} className="text-gray-400" />
                <div>
                  <p className="text-sm font-medium text-gray-800">{server.hostname}</p>
                  <p className="text-xs text-gray-400">{server.ip_address}</p>
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Main Content */}
        <div className="flex-1 p-6">
          {loading && (
            <div className="flex items-center justify-center h-64">
              <p className="text-gray-400">Loading report...</p>
            </div>
          )}

          {!loading && report && (
            <>
              {/* Server Info */}
              <div className="mb-6">
                <h2 className="text-lg font-bold text-gray-900">
                  {report.server.hostname}
                </h2>
                <p className="text-sm text-gray-500">
                  {report.server.ip_address} · Last scanned{' '}
                  {new Date(report.latest_scan.scanned_at).toLocaleString()}
                </p>
              </div>

              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                {/* Score Gauge Card */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm col-span-1">
                  <ScoreGauge score={report.latest_scan.score} />
                </div>

                {/* Critical Failures */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex flex-col justify-center">
                  <div className="flex items-center gap-2 mb-2">
                    <AlertTriangle size={18} className="text-red-500" />
                    <span className="text-sm text-gray-500">Critical Failures</span>
                  </div>
                  <p className="text-4xl font-bold text-red-500">{criticalCount}</p>
                </div>

                {/* Passed Checks */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex flex-col justify-center">
                  <div className="flex items-center gap-2 mb-2">
                    <CheckCircle size={18} className="text-green-500" />
                    <span className="text-sm text-gray-500">Checks Passed</span>
                  </div>
                  <p className="text-4xl font-bold text-green-500">{passedCount}</p>
                </div>

                {/* Total Checks */}
                <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5 flex flex-col justify-center">
                  <div className="flex items-center gap-2 mb-2">
                    <Shield size={18} className="text-blue-500" />
                    <span className="text-sm text-gray-500">Total Checks</span>
                  </div>
                  <p className="text-4xl font-bold text-blue-500">{totalCount}</p>
                </div>
              </div>

              {/* Findings Table */}
              <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-5">
                <h3 className="text-base font-semibold text-gray-800 mb-4">
                  Security Findings
                </h3>
                <FindingsTable findings={report.latest_scan.findings} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}