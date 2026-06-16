import clsx from 'clsx'

interface BadgeProps {
  children: React.ReactNode
  variant?: 'sparse' | 'dense' | 'hybrid' | 'default'
  className?: string
}

export function Badge({ children, variant = 'default', className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
        variant === 'sparse' && 'mode-sparse',
        variant === 'dense' && 'mode-dense',
        variant === 'hybrid' && 'mode-hybrid',
        variant === 'default' && 'bg-slate-100 text-slate-700 border border-slate-200',
        className
      )}
    >
      {children}
    </span>
  )
}
