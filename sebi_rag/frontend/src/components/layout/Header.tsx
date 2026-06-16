import { Shield, Menu } from 'lucide-react'
import { useHealth } from '../../hooks/useHealth'
import { HealthStatus } from '../ui/HealthStatus'

interface HeaderProps {
  onMenuToggle: () => void
}

export function Header({ onMenuToggle }: HeaderProps) {
  const { data: health, isLoading } = useHealth()

  return (
    <header className="sticky top-0 z-50 h-16 bg-sebi flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="md:hidden text-white p-1"
          aria-label="Toggle menu"
        >
          <Menu size={20} />
        </button>
        <Shield className="text-white" size={24} />
        <div>
          <h1 className="text-white font-semibold text-base leading-tight">
            SEBI/RBI Regulatory Intelligence
          </h1>
          <p className="text-white/60 text-xs">
            Hybrid RAG &mdash; BM25 + Vector + Claude Sonnet
          </p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <HealthStatus health={health} isLoading={isLoading} />
        <span className="text-white/40 text-xs hidden sm:block">v1.0.0</span>
      </div>
    </header>
  )
}
