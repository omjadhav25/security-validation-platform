const SEVERITY_STYLES = {
  critical: 'bg-red-100 text-red-700 border border-red-200',
  medium: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  low: 'bg-blue-100 text-blue-700 border border-blue-200',
}

export default function FindingsTable({ findings }) {
  const sorted = [...findings].sort((a, b) => {
    const order = { critical: 0, medium: 1, low: 2 }
    return order[a.severity] - order[b.severity]
  })

  return (
    <div className="overflow-x-auto rounded-xl border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-gray-600 uppercase text-xs">
          <tr>
            <th className="px-4 py-3 text-left">Control</th>
            <th className="px-4 py-3 text-left">Title</th>
            <th className="px-4 py-3 text-left">Severity</th>
            <th className="px-4 py-3 text-left">Status</th>
            <th className="px-4 py-3 text-left">Detail</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {sorted.map((f, i) => (
            <tr key={i} className="hover:bg-gray-50 transition-colors">
              <td className="px-4 py-3 font-mono text-gray-500">{f.control_id}</td>
              <td className="px-4 py-3 font-medium text-gray-800">{f.title}</td>
              <td className="px-4 py-3">
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${SEVERITY_STYLES[f.severity]}`}>
                  {f.severity.toUpperCase()}
                </span>
              </td>
              <td className="px-4 py-3">
                {f.passed ? (
                  <span className="flex items-center gap-1 text-green-600 font-medium">
                    ✅ Pass
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-red-600 font-medium">
                    ❌ Fail
                  </span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-500">{f.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}