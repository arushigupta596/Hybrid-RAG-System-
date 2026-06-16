import clsx from 'clsx'

interface SpinnerProps {
  size?: 'sm' | 'md'
  className?: string
}

export function Spinner({ size = 'md', className }: SpinnerProps) {
  return (
    <div
      className={clsx(
        'animate-spin rounded-full border-2 border-slate-200 border-t-sebi',
        size === 'sm' && 'h-4 w-4',
        size === 'md' && 'h-6 w-6',
        className
      )}
    />
  )
}
