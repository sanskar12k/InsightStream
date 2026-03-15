import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scraperAPI } from '../services/api'
import toast from 'react-hot-toast'

export const useSearches = (limit = 10, offset = 0) => {
  return useQuery({
    queryKey: ['searches', limit, offset],
    queryFn: async () => {
      const response = await scraperAPI.getMySearches({ limit, offset })
      return response.data
    },
  })
}

export const useSearchStatistics = () => {
  return useQuery({
    queryKey: ['search-statistics'],
    queryFn: async () => {
      const response = await scraperAPI.getSearchStatistics()
      return response.data
    },
  })
}

export const useSearchDetail = (searchId) => {
  return useQuery({
    queryKey: ['search', searchId],
    queryFn: async () => {
      const response = await scraperAPI.getSearchStatus(searchId)
      return response.data
    },
    enabled: !!searchId,
    refetchInterval: (data) => {
      // Auto-refetch every 5 seconds if search is in progress
      if (data?.status === 'IN_PROGRESS' || data?.status === 'PENDING') {
        return 5000
      }
      return false
    },
  })
}

export const useInitiateSearch = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (searchData) => {
      const response = await scraperAPI.initiateSearch(searchData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['searches'] })
      toast.success('Search initiated successfully!')
    },
    onError: (error) => {
      const message = error.response?.data?.detail || 'Failed to initiate search'
      toast.error(message)
    },
  })
}

export const useSearchPolling = (searchId, onComplete) => {
  const [isPolling, setIsPolling] = useState(false)

  const { data: search } = useQuery({
    queryKey: ['search', searchId],
    queryFn: async () => {
      const response = await scraperAPI.getSearchStatus(searchId)
      return response.data
    },
    enabled: !!searchId && isPolling,
    refetchInterval: 5000, // Poll every 5 seconds
  })

  useEffect(() => {
    if (search && (search.status === 'COMPLETED' || search.status === 'FAILED')) {
      setIsPolling(false)
      if (onComplete) {
        onComplete(search)
      }
    }
  }, [search, onComplete])

  const startPolling = () => setIsPolling(true)
  const stopPolling = () => setIsPolling(false)

  return { search, isPolling, startPolling, stopPolling }
}
