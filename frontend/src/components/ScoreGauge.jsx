export default function ScoreGauge({ score }) {
  const color = score >= 80 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  const label = score >= 80 ? 'Good' : score >= 50 ? 'Fair' : 'Critical'

  const radius = 80
  const stroke = 12
  const normalizedRadius = radius - stroke / 2
  const circumference = normalizedRadius * 2 * Math.PI
  const half = circumference / 2
  const offset = half - (score / 100) * half

  return (
    <div className="flex flex-col items-center justify-center p-6">
      <svg height={radius + 20} width={radius * 2} viewBox={`0 0 ${radius * 2} ${radius + 20}`}>
        {/* Background arc */}
        <path
          d={`M ${stroke / 2} ${radius} A ${normalizedRadius} ${normalizedRadius} 0 0 1 ${radius * 2 - stroke / 2} ${radius}`}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={stroke}
          strokeLinecap="round"
        />
        {/* Score arc */}
        <path
          d={`M ${stroke / 2} ${radius} A ${normalizedRadius} ${normalizedRadius} 0 0 1 ${radius * 2 - stroke / 2} ${radius}`}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${half} ${half}`}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
        {/* Score text */}
        <text
          x={radius}
          y={radius - 10}
          textAnchor="middle"
          fontSize="28"
          fontWeight="bold"
          fill={color}
        >
          {score}%
        </text>
        <text
          x={radius}
          y={radius + 12}
          textAnchor="middle"
          fontSize="13"
          fill="#6b7280"
        >
          {label}
        </text>
      </svg>
      <p className="text-sm text-gray-500 mt-1">Compliance Score</p>
    </div>
  )
}