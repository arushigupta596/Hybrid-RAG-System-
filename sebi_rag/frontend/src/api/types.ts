export type RetrievalMode = 'sparse' | 'dense' | 'hybrid'

export interface SearchFilters {
  source?: string[]
  category?: string[]
  date_from?: string
  date_to?: string
}

export interface QueryRequest {
  query: string
  mode: RetrievalMode
  top_k?: number
  filters?: SearchFilters
}

export interface ChunkResult {
  chunk_id: string
  doc_id: string
  text: string
  circular_number?: string
  title: string
  section_heading?: string
  source: string
  date_issued?: string
  url: string
  bm25_rank?: number
  vector_rank?: number
  rrf_score: number
  rerank_score?: number
}

export interface QueryResponse {
  query: string
  mode: string
  answer: string
  chunks_used: ChunkResult[]
  all_retrieved: ChunkResult[]
  latency_ms: Record<string, number>
}

export interface SearchResponse {
  query: string
  mode: string
  results: ChunkResult[]
  latency_ms: Record<string, number>
}

export interface HealthResponse {
  status: string
  elasticsearch: boolean
  qdrant: boolean
  postgres: boolean
  version: string
}

export interface PresetQuery {
  label: string
  query: string
  type: 'sparse' | 'dense' | 'hybrid'
}
