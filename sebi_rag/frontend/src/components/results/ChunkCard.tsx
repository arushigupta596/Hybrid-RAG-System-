import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink } from 'lucide-react'
import clsx from 'clsx'
import { Badge } from '../ui/Badge'
import type { ChunkResult } from '../../api/types'

interface ChunkCardProps {
  chunk: ChunkResult
  rank: number
  highlightMode?: 'bm25' | 'vector' | 'both' | 'none'
}

const SOURCE_LABELS: Record<string, string> = {
  sebi_circular: 'SEBI Circular',
  sebi_regulation: 'SEBI Regulation',
  rbi_circular: 'RBI Circular',
  nse_bse: 'NSE/BSE',
}

export function ChunkCard({ chunk, rank, highlightMode = 'none' }: ChunkCardProps) {
  const [expanded, setExpanded] = useState(false)

  const borderClass =
    highlightMode === 'both'
      ? 'border-l-4 border-l-emerald-500'
      : highlightMode === 'bm25'
        ? 'border-l-4 border-l-blue-500'
        : highlightMode === 'vector'
          ? 'border-l-4 border-l-purple-500'
          : 'border border-slate-200'

  const displayText = expanded ? chunk.text : chunk.text.slice(0, 200) + (chunk.text.length > 200 ? '...' : '')

  return (
    <div className={clsx('card p-3', borderClass)}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center justify-center h-6 w-6 rounded-full bg-slate-100 text-xs font-semibold text-slate-700">
            {rank}
          </span>
          <Badge>{SOURCE_LABELS[chunk.source] || chunk.source}</Badge>
          {chunk.circular_number && (
            <span className="text-xs font-mono text-slate-600">{chunk.circular_number}</span>
          )}
          {highlightMode === 'both' && (
            <span className="text-[10px] text-emerald-600 font-medium">In all modes</span>
          )}
        </div>
        {chunk.date_issued && (
          <span className="text-xs text-slate-400 shrink-0">{chunk.date_issued}</span>
        )}
      </div>

      {chunk.section_heading && (
        <p className="text-xs text-slate-500 mt-1 ml-8">{chunk.section_heading}</p>
      )}

      <div className="mt-2 ml-8">
        <p className="text-sm text-slate-700 whitespace-pre-wrap">{displayText}</p>
        {chunk.text.length > 200 && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="btn-ghost text-xs flex items-center gap-1 mt-1"
          >
            {expanded ? <><ChevronUp size={12} /> Collapse</> : <><ChevronDown size={12} /> Expand</>}
          </button>
        )}
      </div>

      <div className="flex items-center gap-2 mt-2 ml-8">
        <Badge>{SOURCE_LABELS[chunk.source] || chunk.source}</Badge>
        {chunk.rerank_score != null && (
          <span className="text-[10px] text-slate-400">score: {chunk.rerank_score.toFixed(3)}</span>
        )}
        {chunk.url && (
          <a
            href={chunk.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-500 flex items-center gap-0.5 hover:underline ml-auto"
          >
            <ExternalLink size={10} /> Source
          </a>
        )}
      </div>
    </div>
  )
}
