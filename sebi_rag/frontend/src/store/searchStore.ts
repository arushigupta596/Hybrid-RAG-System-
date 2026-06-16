import { create } from 'zustand'
import type { RetrievalMode, SearchFilters, QueryResponse } from '../api/types'

interface SearchState {
  query: string
  mode: RetrievalMode
  filters: SearchFilters
  showComparison: boolean
  lastResponse: QueryResponse | null
  setQuery: (q: string) => void
  setMode: (m: RetrievalMode) => void
  setFilters: (f: SearchFilters) => void
  toggleComparison: () => void
  setLastResponse: (r: QueryResponse | null) => void
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  mode: 'hybrid',
  filters: {},
  showComparison: true,
  lastResponse: null,
  setQuery: (query) => set({ query }),
  setMode: (mode) => set({ mode }),
  setFilters: (filters) => set({ filters }),
  toggleComparison: () => set((s) => ({ showComparison: !s.showComparison })),
  setLastResponse: (lastResponse) => set({ lastResponse }),
}))
