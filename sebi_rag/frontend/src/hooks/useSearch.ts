import { useMutation } from '@tanstack/react-query'
import { queryRegulations } from '../api/endpoints'

export function useSearch() {
  return useMutation({
    mutationFn: queryRegulations,
  })
}
