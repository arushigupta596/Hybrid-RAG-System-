import { useState, useCallback } from 'react'
import { Header } from './components/layout/Header'
import { Sidebar } from './components/layout/Sidebar'
import { SearchInput } from './components/search/SearchInput'
import { PresetQueries } from './components/search/PresetQueries'
import { AnswerCard } from './components/results/AnswerCard'
import { LatencyChart } from './components/results/LatencyChart'
import { ComparisonPanel } from './components/results/ComparisonPanel'
import { useSearch } from './hooks/useSearch'
import { useSearchStore } from './store/searchStore'

function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { mode, filters, setQuery, lastResponse, setLastResponse } = useSearchStore()
  const search = useSearch()

  const handleSearch = useCallback(
    (query: string) => {
      setQuery(query)
      search.mutate(
        { query, mode, top_k: 5, filters: Object.keys(filters).length ? filters : undefined },
        {
          onSuccess: (data) => setLastResponse(data),
        }
      )
    },
    [mode, filters, search, setQuery, setLastResponse]
  )

  const handlePresetSelect = useCallback(
    (query: string) => {
      handleSearch(query)
    },
    [handleSearch]
  )

  return (
    <div className="min-h-screen flex flex-col">
      <Header onMenuToggle={() => setSidebarOpen((o) => !o)} />
      <div className="flex flex-1">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <main className="flex-1 max-w-4xl mx-auto px-4 md:px-6 py-4 space-y-4">
          {!lastResponse && !search.isPending && (
            <div className="text-center py-2">
              <h1 className="text-2xl font-bold text-slate-800">Hybrid RAG Search</h1>
              <p className="text-sm text-slate-500 mt-1">
                Search across 1,400+ SEBI and RBI regulatory documents.
              </p>
            </div>
          )}

          <SearchInput
            onSubmit={handleSearch}
            isLoading={search.isPending}
            initialQuery={useSearchStore.getState().query}
          />

          {!lastResponse && !search.isPending && (
            <PresetQueries onSelect={handlePresetSelect} />
          )}

          {search.isError && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg p-3">
              {search.error instanceof Error ? search.error.message : 'Search failed. Please try again.'}
            </div>
          )}

          {search.isPending && (
            <div className="card p-6 space-y-3 animate-pulse">
              <div className="h-4 bg-slate-200 rounded w-3/4" />
              <div className="h-4 bg-slate-200 rounded w-full" />
              <div className="h-4 bg-slate-200 rounded w-5/6" />
              <div className="h-4 bg-slate-200 rounded w-2/3" />
            </div>
          )}

          {lastResponse && !search.isPending && (
            <>
              <AnswerCard response={lastResponse} />
              <LatencyChart latency_ms={lastResponse.latency_ms} />
              <ComparisonPanel response={lastResponse} />
            </>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
