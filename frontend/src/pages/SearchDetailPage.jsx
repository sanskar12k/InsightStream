import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useSearchDetail } from '../hooks/useSearch'
import {
  ArrowLeft,
  Calendar,
  Clock,
  TrendingUp,
  Package,
  Download,
  RefreshCw,
  Table,
} from 'lucide-react'
import { formatDate, formatRelativeTime, getStatusColor, getStatusText } from '../utils/formatters'
import SearchInsights from '../components/SearchInsights'
import { scraperAPI } from '../services/api'
import toast from 'react-hot-toast'

const SearchDetailPage = () => {
  const { searchId } = useParams()
  const navigate = useNavigate()
  const { data: search, isLoading, refetch } = useSearchDetail(searchId)
  const [csvPreview, setCsvPreview] = useState(null)
  const [loadingCsv, setLoadingCsv] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const [generatingInsights, setGeneratingInsights] = useState(false)

  // Fetch CSV preview when search is completed and has output file
  useEffect(() => {
    const fetchCsvPreview = async () => {
      if (search?.status === 'COMPLETED' && search?.output_file_name) {
        setLoadingCsv(true)
        try {
          const response = await scraperAPI.getCsvPreview(searchId)
          setCsvPreview(response.data)
        } catch (error) {
          console.error('Error fetching CSV preview:', error)
          toast.error('Failed to load CSV preview')
        } finally {
          setLoadingCsv(false)
        }
      }
    }

    fetchCsvPreview()
  }, [search, searchId])

  // Poll for insights generation status
  useEffect(() => {
    if (generatingInsights && search?.status === 'COMPLETED') {
      const startTime = Date.now()
      const maxPollDuration = 2.5 * 60 * 1000 // 2.5 minutes in milliseconds

      const interval = setInterval(async () => {
        try {
          // Check if 2.5 minutes have passed
          if (Date.now() - startTime > maxPollDuration) {
            clearInterval(interval)
            setGeneratingInsights(false)
            toast.error('Insights generation timed out. Please try refreshing the page.')
            return
          }

          await refetch()
          const updatedSearch = await scraperAPI.getSearchStatus(searchId)
          if (updatedSearch.data.insight_generated) {
            setGeneratingInsights(false)
            toast.success('Insights generated successfully!')
            refetch()
          }
        } catch (error) {
          console.error('Error polling for insights:', error)
        }
      }, 5000) // Poll every 5 seconds

      return () => clearInterval(interval)
    }
  }, [generatingInsights, search, searchId, refetch])

  // Handle generate insights
  const handleGenerateInsights = async () => {
    setGeneratingInsights(true)
    try {
      await scraperAPI.generateInsights(searchId)
      toast.success('Insights generation started! This may take a few minutes.')
    } catch (error) {
      console.error('Error generating insights:', error)
      toast.error('Failed to generate insights')
      setGeneratingInsights(false)
    }
  }

  // Handle CSV download
  const handleDownload = async () => {
    setDownloading(true)
    try {
      const response = await scraperAPI.downloadCsv(searchId)

      // Create a blob from the response
      const blob = new Blob([response.data], { type: 'text/csv' })
      const url = window.URL.createObjectURL(blob)

      // Create a temporary link and trigger download
      const link = document.createElement('a')
      link.href = url
      link.download = search.output_file_name || 'search_results.csv'
      document.body.appendChild(link)
      link.click()

      // Cleanup
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      toast.success('Download started successfully')
    } catch (error) {
      console.error('Error downloading CSV:', error)
      toast.error('Failed to download CSV file')
    } finally {
      setDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400"></div>
      </div>
    )
  }

  if (!search) {
    return (
      <div className="text-center py-20">
        <Package className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Search Not Found
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          The search you're looking for doesn't exist
        </p>
        <button onClick={() => navigate('/searches')} className="btn-primary">
          Back to Searches
        </button>
      </div>
    )
  }

  const isCompleted = search.status === 'COMPLETED'
  const isInProgress = search.status === 'IN_PROGRESS' || search.status === 'PENDING'
  const isFailed = search.status === 'FAILED'

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <button
        onClick={() => navigate('/searches')}
        className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 transition-colors"
      >
        <ArrowLeft className="w-5 h-5 mr-2" />
        Back to Searches
      </button>

      {/* Header */}
      <div className="card p-6">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
              {search.product_name}
            </h1>
            <div className="flex items-center gap-3">
              <span className={`badge ${getStatusColor(search.status)}`}>
                {getStatusText(search.status)}
              </span>
              {search.category && (
                <span className="badge badge-info">{search.category}</span>
              )}
            </div>
          </div>
          <button
            onClick={() => refetch()}
            className="btn-ghost"
            title="Refresh"
          >
            <RefreshCw className="w-5 h-5" />
          </button>
        </div>

        {/* Progress Bar (for in-progress searches) */}
        {isInProgress && search.progress !== undefined && (
          <div className="mb-6">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-gray-600 dark:text-gray-400 font-medium">Scraping Progress</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  {Math.round(search.progress)}%
                </span>
                <div className="w-1.5 h-1.5 bg-primary-600 dark:bg-primary-400 rounded-full animate-pulse"></div>
              </div>
            </div>
            <div className="relative w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 overflow-hidden">
              {/* Background shimmer effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full animate-shimmer"></div>

              {/* Progress fill with gradient */}
              <div
                className="relative h-3 rounded-full transition-all duration-700 ease-out bg-gradient-to-r from-primary-600 via-primary-500 to-primary-600 dark:from-primary-500 dark:via-primary-400 dark:to-primary-500 animate-gradient-shift"
                style={{
                  width: `${search.progress}%`,
                  backgroundSize: '200% 100%'
                }}
              >
                {/* Shine effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/40 to-transparent animate-shine"></div>
              </div>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
              Scraping in progress...
            </p>
          </div>
        )}

        {/* Search Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="flex items-start space-x-3">
            <div className="bg-primary-100 dark:bg-primary-900 p-2 rounded-lg">
              <TrendingUp className="w-5 h-5 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Platform</p>
              <p className="font-semibold text-gray-900 dark:text-gray-100 capitalize">
                {search.platform?.join(', ') || 'amazon'}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="bg-blue-100 dark:bg-blue-900 p-2 rounded-lg">
              <Calendar className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Started At</p>
              <p className="font-semibold text-gray-900 dark:text-gray-100">
                {formatDate(search.started_at)}
              </p>
            </div>
          </div>

          <div className="flex items-start space-x-3">
            <div className="bg-green-100 dark:bg-green-900 p-2 rounded-lg">
              <Clock className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Last Update</p>
              <p className="font-semibold text-gray-900 dark:text-gray-100">
                {formatRelativeTime(search.started_at)}
              </p>
            </div>
          </div>

          {search.completed_at && (
            <div className="flex items-start space-x-3">
              <div className="bg-purple-100 dark:bg-purple-900 p-2 rounded-lg">
                <Package className="w-5 h-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Completed At</p>
                <p className="font-semibold text-gray-900 dark:text-gray-100">
                  {formatDate(search.completed_at)}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Additional Stats Row */}
        {isCompleted && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-start space-x-3">
              <div className="bg-orange-100 dark:bg-orange-900 p-2 rounded-lg">
                <Package className="w-5 h-5 text-orange-600 dark:text-orange-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Products Scraped</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {search.total_products_scraped || 0}
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className={`p-2 rounded-lg ${search.insight_generated ? 'bg-green-100 dark:bg-green-900' : 'bg-gray-100 dark:bg-gray-700'}`}>
                <TrendingUp className={`w-5 h-5 ${search.insight_generated ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`} />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Insights Status</p>
                <p className={`font-semibold ${search.insight_generated ? 'text-green-600 dark:text-green-400' : 'text-gray-600 dark:text-gray-400'}`}>
                  {search.insight_generated ? 'Generated' : 'Not Generated'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Search Parameters */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Search Parameters
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Max Products:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {search.max_products || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Deep Details:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {search.deep_details ? 'Yes' : 'No'}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Include Reviews:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {search.include_reviews ? 'Yes' : 'No'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Status Messages */}
      {isInProgress && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start">
            <Clock className="w-5 h-5 text-yellow-600 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-yellow-800">
                Scraping in Progress
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                Your search is currently being processed. This may take a few minutes
                depending on the number of products. You can leave this page and come
                back later.
              </p>
            </div>
          </div>
        </div>
      )}

      {isFailed && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start">
            <Package className="w-5 h-5 text-red-600 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-red-800">Search Failed</h3>
              <p className="text-sm text-red-700 mt-1">
                There was an error processing your search. Please try again or
                contact support if the problem persists.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* CSV Preview Section (only for completed searches) */}
      {isCompleted && search.output_file_name && (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <Table className="w-7 h-7" />
              Scraped Data
            </h2>
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="btn-secondary flex items-center gap-2"
            >
              <Download className="w-5 h-5" />
              {downloading ? 'Downloading...' : 'Download Full CSV'}
            </button>
          </div>

          {/* CSV Preview Table */}
          {loadingCsv ? (
            <div className="card p-12 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Loading CSV preview...</p>
            </div>
          ) : csvPreview ? (
            <div className="card overflow-hidden">
              <div className="card-header flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Preview (Top 10 Rows)</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Showing {csvPreview.preview_rows} of {csvPreview.total_rows} total rows
                  </p>
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
                    <tr>
                      {csvPreview.columns.map((column, index) => (
                        <th
                          key={index}
                          className="px-4 py-3 text-left text-xs font-medium text-gray-700 dark:text-gray-300 uppercase tracking-wider whitespace-nowrap"
                        >
                          {column}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                    {csvPreview.rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        {csvPreview.columns.map((column, colIndex) => (
                          <td
                            key={colIndex}
                            className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis"
                            title={row[column]}
                          >
                            {row[column] || '-'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {/* Insights Section */}
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              Insights & Analytics
            </h2>
            {!search.insight_generated && !generatingInsights && search.deep_details && search.include_reviews && (
              <button
                onClick={handleGenerateInsights}
                className="btn-secondary flex items-center gap-2"
              >
                <TrendingUp className="w-5 h-5" />
                Generate Insights
              </button>
            )}
          </div>

          {/* Info message when insights can't be generated */}
          {!search.insight_generated && !generatingInsights && (!search.deep_details || !search.include_reviews) && (
            <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <div className="flex items-start">
                <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400 mr-3 mt-0.5" />
                <div>
                  <h3 className="text-sm font-medium text-blue-800 dark:text-blue-300">
                    Insights Generation Unavailable
                  </h3>
                  <p className="text-sm text-blue-700 dark:text-blue-400 mt-1">
                    Insights generation requires both <strong>Deep Details</strong> and <strong>Include Reviews</strong> to be enabled during the search.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Insights Generation Loader */}
          {generatingInsights && (
            <div className="card p-8 text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-primary-600 dark:border-primary-400 mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Generating Insights...
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                This may take a few minutes. We're analyzing your data to generate brand insights and review summaries.
              </p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 max-w-md mx-auto">
                <div className="bg-primary-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
                You can leave this page and come back later. We'll notify you when insights are ready.
              </p>
            </div>
          )}

          <SearchInsights searchId={search.search_id} generatingInsights={generatingInsights} />
        </>
      )}

      {isCompleted && !search.output_file_name && (
        <div className="card p-8 text-center">
          <Package className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            No Data Available
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            The search completed but no results were generated.
          </p>
        </div>
      )}
    </div>
  )
}

export default SearchDetailPage
