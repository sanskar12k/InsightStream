import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useSearches, useInitiateSearch, useSearchStatistics } from '../hooks/useSearch'
import { Search, TrendingUp, Clock, CheckCircle, AlertCircle, Loader, Package } from 'lucide-react'
import SearchForm from '../components/SearchForm'
import { formatRelativeTime, getStatusColor, getStatusText } from '../utils/formatters'

const DashboardPage = () => {
  const navigate = useNavigate()
  const { user } = useAuth()
  const { data: searchData, isLoading: searchesLoading } = useSearches(5, 0)
  const { data: stats, isLoading: statsLoading } = useSearchStatistics()
  const initiateSearch = useInitiateSearch()
  const [showSearchForm, setShowSearchForm] = useState(false)

  // Extract searches from new response format
  const recentSearches = searchData?.searches || []

  const handleSearchSubmit = async (searchData) => {
    try {
      const result = await initiateSearch.mutateAsync(searchData)
      setShowSearchForm(false)
      // Navigate to the search detail page
      if (result.search_id) {
        navigate(`/search/${result.search_id}`)
      }
    } catch (error) {
      console.error('Search initiation failed:', error)
    }
  }

  // Status icons mapping
  const statusIcons = {
    PENDING: <Clock className="w-4 h-4" />,
    IN_PROGRESS: <Loader className="w-4 h-4 animate-spin" />,
    COMPLETED: <CheckCircle className="w-4 h-4" />,
    FAILED: <AlertCircle className="w-4 h-4" />
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="relative overflow-hidden bg-gradient-to-r from-primary-600 via-primary-700 to-purple-600 rounded-3xl p-8 text-white shadow-2xl">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 animate-pulse"></div>
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full -ml-24 -mb-24"></div>
        <div className="relative z-10">
          <h1 className="text-4xl font-bold mb-2 animate-fade-in">
            Welcome back, {user?.name}! 👋
          </h1>
          <p className="text-primary-100 mb-6 text-lg">
            Start a new search or view your existing searches
          </p>
          <button
            onClick={() => setShowSearchForm(true)}
            className="px-8 py-4 bg-white text-primary-600 rounded-2xl font-semibold hover:bg-gray-100 transition-all duration-300 shadow-xl hover:shadow-2xl hover:scale-105 active:scale-95 inline-flex items-center gap-2"
          >
            <Search className="w-5 h-5" />
            New Search
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6 hover:shadow-primary-500/20 group cursor-pointer">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 font-medium">Total Searches</p>
              <p className="text-4xl font-bold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                {statsLoading ? '...' : stats?.total || 0}
              </p>
            </div>
            <div className="bg-gradient-to-br from-primary-100 to-primary-200 dark:from-primary-900 dark:to-primary-800 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <Search className="w-7 h-7 text-primary-600 dark:text-primary-400" />
            </div>
          </div>
        </div>

        <div className="card p-6 hover:shadow-green-500/20 group cursor-pointer">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 font-medium">Completed</p>
              <p className="text-4xl font-bold text-green-600 dark:text-green-400 group-hover:scale-105 transition-transform">
                {statsLoading ? '...' : stats?.completed || 0}
              </p>
            </div>
            <div className="bg-gradient-to-br from-green-100 to-emerald-200 dark:from-green-900 dark:to-emerald-800 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <CheckCircle className="w-7 h-7 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="card p-6 hover:shadow-yellow-500/20 group cursor-pointer">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 font-medium">In Progress</p>
              <p className="text-4xl font-bold text-yellow-600 dark:text-yellow-400 group-hover:scale-105 transition-transform">
                {statsLoading ? '...' : stats?.in_progress || 0}
              </p>
            </div>
            <div className="bg-gradient-to-br from-yellow-100 to-orange-200 dark:from-yellow-900 dark:to-orange-800 p-4 rounded-2xl group-hover:scale-110 group-hover:animate-pulse transition-transform duration-300 shadow-lg">
              <Clock className="w-7 h-7 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
        </div>

        <div className="card p-6 hover:shadow-red-500/20 group cursor-pointer">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1 font-medium">Failed</p>
              <p className="text-4xl font-bold text-red-600 dark:text-red-400 group-hover:scale-105 transition-transform">
                {statsLoading ? '...' : stats?.failed || 0}
              </p>
            </div>
            <div className="bg-gradient-to-br from-red-100 to-rose-200 dark:from-red-900 dark:to-rose-800 p-4 rounded-2xl group-hover:scale-110 transition-transform duration-300 shadow-lg">
              <AlertCircle className="w-7 h-7 text-red-600 dark:text-red-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Recent Searches */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Recent Searches</h2>
          <button
            onClick={() => navigate('/searches')}
            className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm font-medium"
          >
            View All →
          </button>
        </div>
        <div className="card-body">
          {searchesLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 dark:border-primary-400"></div>
            </div>
          ) : recentSearches.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400 mb-4">No searches yet</p>
              <button
                onClick={() => setShowSearchForm(true)}
                className="btn-primary"
              >
                Create Your First Search
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentSearches.map((search) => (
                <div
                  key={search.search_id}
                  onClick={() => navigate(`/search/${search.search_id}`)}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer transition-colors duration-200"
                >
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                      {search.product_name}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                      <span className="flex items-center">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        {search.platform?.join(', ') || 'amazon'}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-4 h-4 mr-1" />
                        {formatRelativeTime(search.started_at)}
                      </span>
                      {search.status === 'COMPLETED' && search.total_products_scraped && (
                        <span className="flex items-center text-green-600 dark:text-green-400">
                          <Package className="w-4 h-4 mr-1" />
                          {search.total_products_scraped} products
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {statusIcons[search.status]}
                    <span className={`badge ${getStatusColor(search.status)}`}>
                      {getStatusText(search.status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card p-8 cursor-pointer group border-2 border-transparent hover:border-primary-300 dark:hover:border-primary-600">
          <div className="bg-gradient-to-br from-primary-100 to-blue-100 dark:from-primary-900 dark:to-blue-900 w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 shadow-lg">
            <Search className="w-8 h-8 text-primary-600 dark:text-primary-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
            New Search
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
            Start a new product search across multiple platforms
          </p>
          <button
            onClick={() => setShowSearchForm(true)}
            className="text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 font-semibold inline-flex items-center gap-2 group-hover:gap-3 transition-all"
          >
            Get Started
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>

        <div className="card p-8 cursor-pointer group border-2 border-transparent hover:border-purple-300 dark:hover:border-purple-600">
          <div className="bg-gradient-to-br from-purple-100 to-pink-100 dark:from-purple-900 dark:to-pink-900 w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 shadow-lg">
            <TrendingUp className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
            View Insights
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
            Explore detailed analytics and market intelligence
          </p>
          <button
            onClick={() => navigate('/searches')}
            className="text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-semibold inline-flex items-center gap-2 group-hover:gap-3 transition-all"
          >
            View Searches
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>

        <div className="card p-8 cursor-pointer group border-2 border-transparent hover:border-orange-300 dark:hover:border-orange-600">
          <div className="bg-gradient-to-br from-orange-100 to-yellow-100 dark:from-orange-900 dark:to-yellow-900 w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 shadow-lg">
            <Clock className="w-8 h-8 text-orange-600 dark:text-orange-400" />
          </div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2 group-hover:text-orange-600 dark:group-hover:text-orange-400 transition-colors">
            Track Progress
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4 leading-relaxed">
            Monitor your active searches in real-time
          </p>
          <button
            onClick={() => navigate('/searches')}
            className="text-orange-600 dark:text-orange-400 hover:text-orange-700 dark:hover:text-orange-300 font-semibold inline-flex items-center gap-2 group-hover:gap-3 transition-all"
          >
            View Status
            <span className="group-hover:translate-x-1 transition-transform">→</span>
          </button>
        </div>
      </div>

      {/* Search Form Modal */}
      {showSearchForm && (
        <SearchForm
          key={`search-form-${Date.now()}`} // Force fresh mount to refetch usage stats
          onClose={() => setShowSearchForm(false)}
          onSubmit={handleSearchSubmit}
          loading={initiateSearch.isPending}
        />
      )}
    </div>
  )
}

export default DashboardPage
