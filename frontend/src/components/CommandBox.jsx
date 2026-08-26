import { useState } from 'react'
import { Copy, Check } from 'lucide-react'

export default function CommandBox({ label, command }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(command)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div>
      <p className="text-sm font-medium text-slate-700 mb-2">{label}</p>
      <div className="flex items-stretch rounded-lg border border-slate-300 bg-slate-950 overflow-hidden">
        <code className="flex-1 px-3 py-3 text-xs text-slate-100 overflow-x-auto whitespace-pre">
          {command}
        </code>
        <button
          onClick={handleCopy}
          className="px-3 flex items-center justify-center bg-slate-800 hover:bg-slate-700 text-slate-100 shrink-0"
          title="Copy to clipboard"
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
        </button>
      </div>
    </div>
  )
}
