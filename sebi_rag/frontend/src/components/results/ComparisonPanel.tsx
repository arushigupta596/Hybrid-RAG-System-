import { useEffect, useState } from 'react'
import { searchRegulations } from '../../api/endpoints'
import { useSearchStore } from '../../store/searchStore'
import { ChunkCard } from './ChunkCard'
import { Spinner } from '../ui/Spinner'
import type { QueryResponse, SearchResponse, RetrievalMode } from '../../api/types'

interface ComparisonPanelProps {
  response: QueryResponse
}

type AllResults = Record<RetrievalMode, SearchResponse | null>

const MODE_CONFIG: { mode: RetrievalMode; label: string; color: string }[] = [
  { mode: 'sparse', label: 'Sparse (BM25)', color: 'text-blue-600' },
  { mode: 'dense', label: 'Dense (Vector)', color: 'text-purple-600' },
  { mode: 'hybrid', label: 'Hybrid (RRF + Rerank)', color: 'text-emerald-600' },
]

export function ComparisonPanel({ response }: ComparisonPanelProps) {
  const { showComparison, filters } = useSearchStore()
  const [results, setResults] = useState<AllResults>({ sparse: null, dense: null, hybrid: null })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!showComparison || !response.query) return

    setLoading(true)
    Promise.all([
      searchRegulations({ query: response.query, mode: 'sparse', top_k: 5, filters }).catch(() => null),
      searchRegulations({ query: response.query, mode: 'dense', top_k: 5, filters }).catch(() => null),
      searchRegulations({ query: response.query, mode: 'hybrid', top_k: 5, filters }).catch(() => null),
    ]).then(([sparse, dense, hybrid]) => {
      setResults({ sparse, dense, hybrid })
      setLoading(false)
    })
  }, [response.query, showComparison, filters])

  if (!showComparison) return null

  if (loading) {
    return (
      <div className="card p-6 flex items-center justify-center gap-2">
        <Spinner size="sm" />
        <span className="text-sm text-slate-500">Comparing retrieval modes...</span>
      </div>
    )
  }

  const chunkModes: Record<string, Set<string>> = {}
  for (const [mode, res] of Object.entries(results)) {
    if (!res) continue
    for (const r of res.results) {
      if (!chunkModes[r.chunk_id]) chunkModes[r.chunk_id] = new Set()
      chunkModes[r.chunk_id].add(mode)
    }
  }

  const getHighlightMode = (chunkId: string, currentMode: string): 'bm25' | 'vector' | 'both' | 'none' => {
    const modes = chunkModes[chunkId]
    if (!modes) return 'none'
    if (modes.size >= 3) return 'both'
    if (modes.size === 1) {
      if (currentMode === 'sparse') return 'bm25'
      if (currentMode === 'dense') return 'vector'
      return 'none'
    }
    return 'none'
  }

  const allInAll = Object.values(chunkModes).filter((s) => s.size >= 3).length
  const uniqueSparse = Object.entries(chunkModes).filter(([, s]) => s.size === 1 && s.has('sparse')).length
  const uniqueDense = Object.entries(chunkModes).filter(([, s]) => s.size === 1 && s.has('dense')).length

  return (
    <div className="card p-5">
      <h3 className="text-sm font-semibold text-slate-700 mb-4">Retrieval Comparison</h3>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {MODE_CONFIG.map(({ mode, label, color }) => {
          const res = results[mode]
          return (
            <div key={mode}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-xs font-semibold ${color}`}>{label}</span>
                {res && (
                  <span className="text-[10px] text-slate-400">
                    {res.latency_ms.total || Object.values(res.latency_ms).reduce((a, b) => a + b, 0)}ms
                  </span>
                )}
              </div>
              <div className="space-y-2">
                {res ? (
                  res.results.map((chunk, i) => (
                    <ChunkCard
                      key={chunk.chunk_id}
                      chunk={chunk}
                      rank={i + 1}
                      highlightMode={getHighlightMode(chunk.chunk_id, mode)}
                    />
                  ))
                ) : (
                  <p className="text-xs text-slate-400">No results</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
      <p className="text-xs text-slate-500 mt-3 text-center">
        {allInAll} results appear in all 3 modes &middot; {uniqueSparse} unique to sparse &middot; {uniqueDense} unique to dense
      </p>
    </div>
  )
}
