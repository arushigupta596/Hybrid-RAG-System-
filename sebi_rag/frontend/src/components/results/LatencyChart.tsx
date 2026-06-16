import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface LatencyChartProps {
  latency_ms: Record<string, number>
  comparisonLatencies?: Record<string, Record<string, number>>
}

const COLORS: Record<string, string> = {
  sparse: '#2563eb',
  dense: '#9333ea',
  hybrid: '#059669',
}

export function LatencyChart({ latency_ms, comparisonLatencies }: LatencyChartProps) {
  const data: { name: string; bm25: number; vector: number; rerank: number; llm: number; total: number; color: string }[] = []

  if (comparisonLatencies) {
    for (const [mode, lat] of Object.entries(comparisonLatencies)) {
      data.push({
        name: mode.charAt(0).toUpperCase() + mode.slice(1),
        bm25: lat.bm25 || 0,
        vector: lat.vector || 0,
        rerank: lat.rerank || 0,
        llm: lat.llm || 0,
        total: lat.total || Object.values(lat).reduce((a, b) => a + b, 0),
        color: COLORS[mode] || '#666',
      })
    }
  }

  data.push({
    name: 'Hybrid (answer)',
    bm25: latency_ms.bm25 || 0,
    vector: latency_ms.vector || 0,
    rerank: latency_ms.rerank || 0,
    llm: latency_ms.llm || 0,
    total: latency_ms.total || 0,
    color: COLORS.hybrid,
  })

  return (
    <div className="card p-4">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Latency Breakdown</h3>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} layout="vertical" margin={{ left: 80, right: 40 }}>
          <XAxis type="number" tickFormatter={(v) => `${v}ms`} fontSize={11} />
          <YAxis type="category" dataKey="name" fontSize={11} width={80} />
          <Tooltip formatter={(val: number) => `${val}ms`} />
          <Legend iconSize={10} wrapperStyle={{ fontSize: 11 }} />
          <Bar dataKey="bm25" stackId="a" fill="#3b82f6" name="BM25" />
          <Bar dataKey="vector" stackId="a" fill="#9333ea" name="Vector" />
          <Bar dataKey="rerank" stackId="a" fill="#f59e0b" name="Rerank" />
          <Bar dataKey="llm" stackId="a" fill="#ef4444" name="LLM" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
