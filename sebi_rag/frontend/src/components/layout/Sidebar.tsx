import { useState } from 'react'
import { ChevronDown, ChevronRight, X } from 'lucide-react'
import clsx from 'clsx'
import { useSearchStore } from '../../store/searchStore'
import { Toggle } from '../ui/Toggle'
import type { RetrievalMode } from '../../api/types'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

const MODES: { value: RetrievalMode; label: string; desc: string; color: string; recommended?: boolean }[] = [
  { value: 'hybrid', label: 'Hybrid', desc: 'BM25 + Vector + Rerank', color: 'border-l-emerald-500', recommended: true },
  { value: 'sparse', label: 'Sparse', desc: 'Keyword + exact match', color: 'border-l-blue-500' },
  { value: 'dense', label: 'Dense', desc: 'Semantic search', color: 'border-l-purple-500' },
]

const SOURCES = [
  { value: 'sebi_circular', label: 'SEBI Circulars' },
  { value: 'sebi_regulation', label: 'SEBI Regulations' },
  { value: 'rbi_circular', label: 'RBI Circulars' },
  { value: 'nse_bse', label: 'NSE/BSE' },
]

const CATEGORIES = [
  'Mutual Funds', 'IPO', 'LODR', 'ICDR', 'SAST', 'FPI', 'AIF', 'Banking', 'PMS', 'Derivatives',
]

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { mode, setMode, filters, setFilters, showComparison, toggleComparison } = useSearchStore()
  const [filtersOpen, setFiltersOpen] = useState(true)
  const [aboutOpen, setAboutOpen] = useState(false)

  const hasActiveFilters = !!(
    filters.source?.length ||
    filters.category?.length ||
    filters.date_from ||
    filters.date_to
  )

  const toggleSource = (src: string) => {
    const current = filters.source || []
    const next = current.includes(src)
      ? current.filter((s) => s !== src)
      : [...current, src]
    setFilters({ ...filters, source: next.length ? next : undefined })
  }

  const toggleCategory = (cat: string) => {
    const current = filters.category || []
    const next = current.includes(cat)
      ? current.filter((c) => c !== cat)
      : [...current, cat]
    setFilters({ ...filters, category: next.length ? next : undefined })
  }

  return (
    <>
      {isOpen && (
        <div className="fixed inset-0 bg-black/30 z-40 md:hidden" onClick={onClose} />
      )}
      <aside
        className={clsx(
          'fixed md:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)] w-[260px] bg-white border-r border-slate-200 overflow-y-auto transition-transform',
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        )}
      >
        <div className="p-4 space-y-4">
          <button className="md:hidden absolute top-2 right-2 text-slate-400" onClick={onClose}>
            <X size={18} />
          </button>

          {/* Retrieval Mode */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Retrieval Mode</h3>
            <div className="space-y-1">
              {MODES.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setMode(m.value)}
                  className={clsx(
                    'w-full text-left px-2.5 py-2 rounded-lg border-l-[3px] transition-all',
                    mode === m.value
                      ? `${m.color} bg-slate-50 border border-slate-200`
                      : 'border-l-transparent hover:bg-slate-50'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span className={clsx(
                      'h-3 w-3 rounded-full border-2 shrink-0',
                      mode === m.value ? 'border-sebi bg-sebi' : 'border-slate-300'
                    )} />
                    <span className="font-medium text-sm">{m.label}</span>
                    {m.recommended && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                        Recommended
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500 ml-5">{m.desc}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div>
            <button
              onClick={() => setFiltersOpen(!filtersOpen)}
              className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wider w-full"
            >
              {filtersOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              Filters
            </button>
            {filtersOpen && (
              <div className="mt-2 space-y-2.5">
                <div>
                  <p className="text-xs text-slate-500 mb-0.5">Source</p>
                  {SOURCES.map((s) => (
                    <label key={s.value} className="flex items-center gap-2 text-sm leading-6 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={filters.source?.includes(s.value) || false}
                        onChange={() => toggleSource(s.value)}
                        className="rounded border-slate-300"
                      />
                      {s.label}
                    </label>
                  ))}
                </div>

                <div>
                  <p className="text-xs text-slate-500 mb-1">Category</p>
                  <div className="flex flex-wrap gap-1">
                    {CATEGORIES.map((cat) => (
                      <button
                        key={cat}
                        onClick={() => toggleCategory(cat)}
                        className={clsx(
                          'text-xs px-2 py-1 rounded-full border transition-colors',
                          filters.category?.includes(cat)
                            ? 'bg-sebi text-white border-sebi'
                            : 'border-slate-200 text-slate-600 hover:border-slate-300'
                        )}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-slate-500">From</label>
                    <input
                      type="date"
                      value={filters.date_from || ''}
                      onChange={(e) => setFilters({ ...filters, date_from: e.target.value || undefined })}
                      className="w-full text-xs border border-slate-200 rounded px-2 py-1"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500">To</label>
                    <input
                      type="date"
                      value={filters.date_to || ''}
                      onChange={(e) => setFilters({ ...filters, date_to: e.target.value || undefined })}
                      className="w-full text-xs border border-slate-200 rounded px-2 py-1"
                    />
                  </div>
                </div>

                {hasActiveFilters && (
                  <button
                    onClick={() => setFilters({})}
                    className="btn-ghost text-xs text-red-500"
                  >
                    Clear filters
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Options */}
          <div>
            <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Options</h3>
            <Toggle
              checked={showComparison}
              onChange={toggleComparison}
              label="Show comparison panel"
            />
          </div>

          {/* About */}
          <div>
            <button
              onClick={() => setAboutOpen(!aboutOpen)}
              className="flex items-center gap-1 text-xs font-semibold text-slate-500 uppercase tracking-wider w-full"
            >
              {aboutOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
              About
            </button>
            {aboutOpen && (
              <div className="mt-2 text-xs text-slate-500 space-y-2">
                <p>
                  Hybrid RAG system demonstrating that combining keyword and semantic retrieval outperforms
                  either approach alone on regulatory compliance queries.
                </p>
                <div className="flex flex-wrap gap-1">
                  {['Elasticsearch', 'Qdrant', 'Claude Sonnet 4.6', 'RRF Fusion'].map((t) => (
                    <span key={t} className="px-2 py-0.5 bg-slate-100 rounded text-[10px]">{t}</span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}
