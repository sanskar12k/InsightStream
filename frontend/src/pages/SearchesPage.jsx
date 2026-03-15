import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSearches } from '../hooks/useSearch'
import {
  Search,
  Filter,
  TrendingUp,
  Clock,
  Calendar,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react'
import { formatDate, formatRelativeTime, getStatusColor, getStatusText } from '../utils/formatters'

const SearchesPage = () => {
  const navigate = useNavigate()
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const { data: searchData, isLoading } = useSearches(itemsPerPage, (currentPage - 1) * itemsPerPage)
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')

  // Extract data from new response format
  const searches = searchData?.searches || []
  const totalSearches = searchData?.total || 0
  const totalPages = Math.ceil(totalSearches / itemsPerPage)

  // Filter searches
  const filteredSearches = searches?.filter((search) => {
    const matchesStatus = statusFilter === 'ALL' || search.status === statusFilter
    const matchesQuery =
      searchQuery === '' ||
      search.product_name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchesStatus && matchesQuery
  }) || []

  const statusOptions = [
    { value: 'ALL', label: 'All Status' },
    { value: 'PENDING', label: 'Pending' },
    { value: 'IN_PROGRESS', label: 'In Progress' },
    { value: 'COMPLETED', label: 'Completed' },
    { value: 'FAILED', label: 'Failed' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">My Searches</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            View and manage all your product searches
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search Input */}
          <div className="flex-1">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              </div>
              <input
                type="text"
                placeholder="Search by product name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="w-full md:w-48">
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Filter className="h-5 w-5 text-gray-400 dark:text-gray-500" />
              </div>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="input-field pl-10 appearance-none cursor-pointer"
              >
                {statusOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Results Count & Items Per Page */}
        <div className="mt-4 flex items-center justify-between">
          <div className="text-sm text-gray-600 dark:text-gray-400">
            Showing {Math.min((currentPage - 1) * itemsPerPage + 1, totalSearches)}-{Math.min(currentPage * itemsPerPage, totalSearches)} of {totalSearches} searches
            {(statusFilter !== 'ALL' || searchQuery) && ` (${filteredSearches.length} filtered)`}
          </div>

          {/* Items per page selector */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 dark:text-gray-400">Per page:</label>
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value))
                setCurrentPage(1) // Reset to first page when changing items per page
              }}
              className="input-field py-1 px-2 text-sm"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Searches List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
        </div>
      ) : filteredSearches.length === 0 ? (
        <div className="card p-12 text-center">
          <Search className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {searchQuery || statusFilter !== 'ALL' ? 'No searches found' : 'No searches yet'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchQuery || statusFilter !== 'ALL'
              ? 'Try adjusting your filters'
              : 'Start by creating your first product search'}
          </p>
          {!searchQuery && statusFilter === 'ALL' && (
            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary"
            >
              Create New Search
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredSearches.map((search, index) => (
            <div
              key={search.search_id}
              onClick={() => navigate(`/search/${search.search_id}`)}
              className="card p-6 cursor-pointer group relative overflow-hidden"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-primary-50/0 via-primary-50/50 to-primary-50/0 dark:from-primary-900/0 dark:via-primary-900/30 dark:to-primary-900/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
              <div className="flex items-start justify-between relative z-10">
                <div className="flex-1">
                  {/* Product Name & Status */}
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors group-hover:scale-105 inline-block">
                      {search.product_name}
                    </h3>
                    <span className={`badge ${getStatusColor(search.status)} shadow-md`}>
                      {getStatusText(search.status)}
                    </span>
                  </div>

                  {/* Meta Information */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600 dark:text-gray-400">
                    <div className="flex items-center">
                      <TrendingUp className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
                      <span>
                        <span className="font-medium">Platform:</span>{' '}
                        {search.platform?.join(', ') || 'amazon'}
                      </span>
                    </div>

                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
                      <span>
                        <span className="font-medium">Started:</span>{' '}
                        {formatDate(search.started_at)}
                      </span>
                    </div>

                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-2 text-gray-400 dark:text-gray-500" />
                      <span>
                        <span className="font-medium">Last Update:</span>{' '}
                        {formatRelativeTime(search.started_at)}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar (for in-progress searches) */}
                  {(search.status === 'IN_PROGRESS' || search.status === 'PENDING') &&
                    search.progress !== undefined && (
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-sm mb-2">
                          <span className="text-gray-600 dark:text-gray-400 font-medium">Progress</span>
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gray-900 dark:text-gray-100">
                              {Math.round(search.progress)}%
                            </span>
                            {search.status === 'IN_PROGRESS' && (
                              <div className="w-1.5 h-1.5 bg-primary-600 dark:bg-primary-400 rounded-full animate-pulse"></div>
                            )}
                          </div>
                        </div>
                        <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
                          {/* Background shimmer effect */}
                          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-shimmer"></div>

                          {/* Progress fill with gradient */}
                          <div
                            className="relative h-2.5 rounded-full transition-all duration-700 ease-out bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600 dark:from-primary-500 dark:via-primary-400 dark:to-primary-500 animate-gradient-shift"
                            style={{
                              width: `${search.progress}%`,
                              backgroundSize: '200% 100%'
                            }}
                          >
                            {/* Shine effect */}
                            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shine"></div>
                          </div>
                        </div>

                        {/* Status text */}
                        {search.status === 'IN_PROGRESS' && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                            Scraping in progress...
                          </p>
                        )}
                      </div>
                    )}

                  {/* Category Badge (if available) */}
                  {search.category && (
                    <div className="mt-3">
                      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {search.category}
                      </span>
                    </div>
                  )}
                </div>

                {/* Arrow Icon */}
                <div className="ml-4 relative z-10">
                  <ChevronRight className="w-6 h-6 text-gray-400 dark:text-gray-500 group-hover:text-primary-600 dark:group-hover:text-primary-400 group-hover:translate-x-2 transition-all duration-300" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {!isLoading && filteredSearches.length > 0 && totalPages > 1 && (
        <div className="card p-4">
          <div className="flex items-center justify-between">
            {/* Previous Button */}
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              Previous
            </button>

            {/* Page Numbers */}
            <div className="flex items-center gap-2">
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                let pageNumber
                if (totalPages <= 7) {
                  pageNumber = i + 1
                } else if (currentPage <= 4) {
                  pageNumber = i + 1
                } else if (currentPage >= totalPages - 3) {
                  pageNumber = totalPages - 6 + i
                } else {
                  pageNumber = currentPage - 3 + i
                }

                return (
                  <button
                    key={pageNumber}
                    onClick={() => setCurrentPage(pageNumber)}
                    className={`w-10 h-10 rounded-lg font-medium transition-colors ${
                      currentPage === pageNumber
                        ? 'bg-primary-600 text-white'
                        : 'bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                    }`}
                  >
                    {pageNumber}
                  </button>
                )
              })}
              {totalPages > 7 && currentPage < totalPages - 3 && (
                <>
                  <span className="text-gray-500">...</span>
                  <button
                    onClick={() => setCurrentPage(totalPages)}
                    className="w-10 h-10 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 font-medium transition-colors"
                  >
                    {totalPages}
                  </button>
                </>
              )}
            </div>

            {/* Next Button */}
            <button
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* Page Info */}
          <div className="text-center mt-3 text-sm text-gray-600 dark:text-gray-400">
            Page {currentPage} of {totalPages}
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchesPage
