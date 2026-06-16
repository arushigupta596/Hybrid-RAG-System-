import clsx from 'clsx'
import type { PresetQuery } from '../../api/types'

interface PresetQueriesProps {
  onSelect: (query: string) => void
}

export const PRESET_QUERIES: PresetQuery[] = [
  { label: 'SEBI Buyback Regulations', query: 'What are the key regulations governing buyback of shares under SEBI?', type: 'sparse' },
  { label: 'UAPA Section 51-A compliance', query: 'What are the obligations under Section 51-A of UAPA for financial institutions?', type: 'sparse' },
  { label: 'RBI ECB policy all-in-cost', query: 'What is the all-in-cost ceiling under RBI external commercial borrowing policy?', type: 'sparse' },
  { label: 'KYC anti-money laundering', query: 'What are the KYC and anti-money laundering guidelines for NBFCs?', type: 'dense' },
  { label: 'NRI property acquisition', query: 'What rules govern acquisition of immovable property in India by NRIs and foreign nationals?', type: 'dense' },
  { label: 'Sovereign Gold Bonds', query: 'What are the terms and conditions of the Sovereign Gold Bond scheme?', type: 'dense' },
  { label: 'Buyback offer size limits', query: 'What is the maximum permissible buyback size and how is it calculated under SEBI regulations?', type: 'hybrid' },
  { label: 'Non-resident shareholder tender', query: 'What documents must non-resident shareholders submit when tendering shares in a buyback?', type: 'hybrid' },
  { label: 'NBFC prudential norms', query: 'What are the prudential norms and capital adequacy requirements for non-banking financial companies?', type: 'hybrid' },
]

const TYPE_LABELS: Record<string, { label: string; color: string; border: string }> = {
  sparse: { label: 'SPARSE WINS — EXACT MATCH', color: 'text-blue-600', border: 'hover:border-l-blue-500' },
  dense: { label: 'DENSE WINS — SEMANTIC', color: 'text-purple-600', border: 'hover:border-l-purple-500' },
  hybrid: { label: 'HYBRID WINS — BOTH', color: 'text-emerald-600', border: 'hover:border-l-emerald-500' },
}

export function PresetQueries({ onSelect }: PresetQueriesProps) {
  const groups = ['sparse', 'dense', 'hybrid'] as const

  return (
    <div className="space-y-2">
      {groups.map((type) => {
        const meta = TYPE_LABELS[type]
        const queries = PRESET_QUERIES.filter((q) => q.type === type)
        return (
          <div key={type}>
            <h3 className={clsx('text-sm font-semibold tracking-wider mb-1', meta.color)}>
              {meta.label}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-1.5">
              {queries.map((q) => (
                <button
                  key={q.label}
                  onClick={() => onSelect(q.query)}
                  className={clsx(
                    'btn-ghost text-left border-l-2 border-l-transparent',
                    meta.border,
                    'hover:bg-slate-50'
                  )}
                >
                  {q.label}
                </button>
              ))}
            </div>
          </div>
        )
      })}
    </div>
  )
}
