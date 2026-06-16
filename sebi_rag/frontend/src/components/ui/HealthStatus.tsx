import type { HealthResponse } from '../../api/types'

interface HealthStatusProps {
  health: HealthResponse | undefined
  isLoading: boolean
}

function Dot({ ok, label }: { ok: boolean | undefined; label: string }) {
  const color =
    ok === undefined ? 'bg-slate-400' : ok ? 'bg-emerald-400' : 'bg-red-400'
  const tooltip =
    ok === undefined ? `${label}: Unknown` : ok ? `${label}: OK` : `${label}: Down`

  return (
    <div className="flex items-center gap-1" title={tooltip}>
      <span className={`h-2 w-2 rounded-full ${color}`} />
      <span className="text-xs text-white/70">{label}</span>
    </div>
  )
}

export function HealthStatus({ health, isLoading }: HealthStatusProps) {
  if (isLoading) {
    return (
      <div className="flex items-center gap-3">
        <Dot ok={undefined} label="ES" />
        <Dot ok={undefined} label="Qdrant" />
        <Dot ok={undefined} label="DB" />
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3">
      <Dot ok={health?.elasticsearch} label="ES" />
      <Dot ok={health?.qdrant} label="Qdrant" />
      <Dot ok={health?.postgres} label="DB" />
    </div>
  )
}
