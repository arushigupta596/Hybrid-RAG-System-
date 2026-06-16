import { api } from './client'
import type { QueryRequest, QueryResponse, SearchResponse, HealthResponse } from './types'

export const queryRegulations = (req: QueryRequest): Promise<QueryResponse> =>
  api.post<QueryResponse>('/api/v1/query', req).then(r => r.data)

export const searchRegulations = (req: QueryRequest): Promise<SearchResponse> =>
  api.post<SearchResponse>('/api/v1/search', req).then(r => r.data)

export const fetchHealth = (): Promise<HealthResponse> =>
  api.get<HealthResponse>('/api/v1/health').then(r => r.data)
