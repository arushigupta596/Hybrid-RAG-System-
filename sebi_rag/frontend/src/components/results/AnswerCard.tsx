import { useState } from 'react'
import { Streamdown } from 'streamdown'
import { ChevronDown, ChevronUp, Clock } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { ChunkCard } from './ChunkCard'
import type { QueryResponse } from '../../api/types'

interface AnswerCardProps {
  response: QueryResponse
}


export function AnswerCard({ response }: AnswerCardProps) {
  const [sourcesOpen, setSourcesOpen] = useState(false)


  const latencyEntries = Object.entries(response.latency_ms).filter(([k]) => k !== 'total')
  const totalMs = response.latency_ms.total || 0

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-slate-800">Answer</h2>
        <div className="flex items-center gap-2">
          <div className="group relative">
            <span className="flex items-center gap-1 text-xs text-slate-400 cursor-help">
              <Clock size={12} /> {totalMs}ms total
            </span>
            <div className="absolute right-0 top-full mt-1 bg-slate-800 text-white text-xs rounded-lg p-2 hidden group-hover:block z-10 whitespace-nowrap">
              {latencyEntries.map(([key, val]) => (
                <div key={key} className="flex justify-between gap-4">
                  <span className="capitalize">{key}</span>
                  <span>{val}ms</span>
                </div>
              ))}
            </div>
          </div>
          <Badge variant={response.mode as 'sparse' | 'dense' | 'hybrid'}>
            {response.mode}
          </Badge>
        </div>
      </div>

      <div className="text-slate-700">
        <Streamdown>{response.answer}</Streamdown>
      </div>

      <div className="mt-4 border-t border-slate-100 pt-3">
        <button
          onClick={() => setSourcesOpen(!sourcesOpen)}
          className="btn-ghost flex items-center gap-1 text-xs"
        >
          {sourcesOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          Sources used ({response.chunks_used.length} chunks)
        </button>
        {sourcesOpen && (
          <div className="mt-2 space-y-2">
            {response.chunks_used.map((chunk, i) => (
              <ChunkCard key={chunk.chunk_id} chunk={chunk} rank={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
