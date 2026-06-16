import { useState, useRef, useEffect } from 'react'
import { Search } from 'lucide-react'
import { Spinner } from '../ui/Spinner'

interface SearchInputProps {
  onSubmit: (query: string) => void
  isLoading: boolean
  initialQuery?: string
}

export function SearchInput({ onSubmit, isLoading, initialQuery }: SearchInputProps) {
  const [value, setValue] = useState(initialQuery || '')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (initialQuery !== undefined) {
      setValue(initialQuery)
    }
  }, [initialQuery])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (trimmed && !isLoading) {
      onSubmit(trimmed)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="card p-4">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask about SEBI or RBI regulations..."
        rows={2}
        className="w-full resize-none border border-slate-200 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 transition-shadow"
      />
      <div className="flex items-center justify-between mt-2">
        <span className="text-xs text-slate-400">
          {value.length}/500
        </span>
        <button
          onClick={handleSubmit}
          disabled={isLoading || !value.trim()}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <Spinner size="sm" />
          ) : (
            <Search size={16} />
          )}
          Search Regulations
        </button>
      </div>
    </div>
  )
}
