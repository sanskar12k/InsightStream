import { useState, useEffect } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
import { TrendingUp, Package, Star, DollarSign, Award, AlertCircle, Loader } from 'lucide-react'
import { scraperAPI } from '../services/api'
import toast from 'react-hot-toast'

const SearchInsights = ({ searchId, generatingInsights = false }) => {
  const [activeTab, setActiveTab] = useState('overview')
  const [brandInsights, setBrandInsights] = useState(null)
  const [reviewAnalysis, setReviewAnalysis] = useState(null)
  const [silverData, setSilverData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch insights data
  useEffect(() => {
    const fetchInsights = async () => {
      setLoading(true)
      setError(null)
      try {
        const [brandRes, reviewRes, silverRes] = await Promise.all([
          scraperAPI.getBrandInsights(searchId).catch(err => ({ data: null, error: err })),
          scraperAPI.getReviewAnalysis(searchId).catch(err => ({ data: null, error: err })),
          scraperAPI.getSilverData(searchId, { limit: 100, offset: 0 }).catch(err => ({ data: null, error: err })),
        ])

        if (brandRes.data) setBrandInsights(brandRes.data)
        if (reviewRes.data) setReviewAnalysis(reviewRes.data)
        if (silverRes.data) setSilverData(silverRes.data)

        if (!brandRes.data && !reviewRes.data && !silverRes.data) {
          setError('No insights data available. Please generate insights first.')
        }
      } catch (err) {
        console.error('Error fetching insights:', err)
        setError('Failed to load insights data')
        toast.error('Failed to load insights')
      } finally {
        setLoading(false)
      }
    }

    if (searchId) {
      fetchInsights()
    }
  }, [searchId])

  // Process data for visualizations
  const processedData = () => {
    if (!brandInsights && !silverData) return null

    const brands = brandInsights?.brands || []
    const products = silverData?.products || []

    // Calculate summary statistics
    const totalProducts = silverData?.total_products || 0
    const avgPrice = products.length > 0
      ? products.reduce((sum, p) => sum + (parseFloat(p.Current_Price) || 0), 0) / products.length
      : 0
    const avgRating = products.length > 0
      ? products.reduce((sum, p) => sum + (parseFloat(p.Rating) || 0), 0) / products.length
      : 0
    const topBrand = brands.length > 0 ? brands[0].Brand : 'N/A'

    return {
      summary: {
        totalProducts,
        avgPrice,
        avgRating,
        topBrand,
      },
      brands,
      products,
    }
  }

  const insights = processedData()

  const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'brands', label: 'Brand Analysis' },
    { id: 'reviews', label: 'Review Analysis' },
    { id: 'products', label: 'Product Details' },
  ]

  // Loading state
  if (loading) {
    return (
      <div className="card p-12 text-center">
        <Loader className="w-12 h-12 text-primary-600 dark:text-primary-400 mx-auto mb-4 animate-spin" />
        <p className="text-gray-600 dark:text-gray-400">Loading insights...</p>
      </div>
    )
  }

  // Error state - only show if not currently generating
  if ((error || !insights) && !generatingInsights) {
    return (
      <div className="card p-12 text-center">
        <AlertCircle className="w-12 h-12 text-yellow-600 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          {error || 'Insights Not Available'}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          The insights data hasn't been generated yet. Please click the "Generate Insights" button above to start the process.
        </p>
      </div>
    )
  }

  // Don't show anything if insights are being generated
  if (generatingInsights || !insights) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200">
          <div className="flex overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <Package className="w-8 h-8 text-primary-600 dark:text-primary-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Total</span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {insights.summary.totalProducts}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Products Found</p>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <DollarSign className="w-8 h-8 text-green-600 dark:text-green-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Average</span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                ₹{insights.summary.avgPrice.toFixed(0)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Avg. Price</p>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <Star className="w-8 h-8 text-yellow-600 dark:text-yellow-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Average</span>
              </div>
              <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {insights.summary.avgRating.toFixed(1)}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Avg. Rating</p>
            </div>

            <div className="card p-6">
              <div className="flex items-center justify-between mb-2">
                <Award className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                <span className="text-xs text-gray-500 dark:text-gray-400">Top Brand</span>
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {insights.summary.topBrand}
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Highest Ranked</p>
            </div>
          </div>

          {/* Top Brands */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Top Brands by Rank</h3>
            </div>
            <div className="card-body">
              <div className="space-y-4">
                {insights.brands.slice(0, 10).map((brand, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="flex items-center justify-center w-8 h-8 bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-400 rounded-full font-bold">
                        {parseInt(brand.brand_rank)}
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                          {brand.Brand}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {brand.product_count} products • {parseFloat(brand.avg_review_count).toFixed(0)} avg reviews
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-6">
                      <div className="text-right">
                        <p className="font-semibold text-gray-900 dark:text-gray-100 flex items-center">
                          <Star className="w-4 h-4 text-yellow-500 mr-1 fill-current" />
                          {parseFloat(brand.brand_rating).toFixed(2)}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Rating</p>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold text-gray-900 dark:text-gray-100">
                          {parseFloat(brand.trust_score).toFixed(1)}%
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">Trust Score</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Brand Analysis Tab */}
      {activeTab === 'brands' && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Brand Distribution Pie Chart */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Brand Distribution (Top 10)
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={insights.brands.slice(0, 10).map(b => ({
                      name: b.Brand,
                      value: parseInt(b.product_count)
                    }))}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {insights.brands.slice(0, 10).map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Brand Performance Radar Chart */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Top Brands - Multi-Dimensional Analysis
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Comparing brands across rating, trust score, product count, and reviews
              </p>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={(() => {
                  const topBrands = insights.brands.slice(0, 6)
                  const maxProductCount = Math.max(...topBrands.map(b => parseInt(b.product_count)))
                  const maxAvgReviews = Math.max(...topBrands.map(b => parseFloat(b.avg_review_count)))

                  return topBrands.map((b, index) => ({
                    brand: b.Brand.length > 12 ? b.Brand.substring(0, 12) + '...' : b.Brand,
                    fullBrand: b.Brand,
                    'Rating': parseFloat(b.brand_rating) * 20, // Scale to 0-100
                    'Trust Score': parseFloat(b.trust_score),
                    'Product Count': (parseInt(b.product_count) / maxProductCount) * 100,
                    'Avg Reviews': (parseFloat(b.avg_review_count) / maxAvgReviews) * 100,
                    actualRating: parseFloat(b.brand_rating).toFixed(2),
                    actualTrust: parseFloat(b.trust_score).toFixed(1),
                    actualProducts: parseInt(b.product_count),
                    actualReviews: parseFloat(b.avg_review_count).toFixed(0)
                  }))
                })()}>
                  <PolarGrid stroke="#e5e7eb" className="dark:stroke-gray-600" />
                  <PolarAngleAxis
                    dataKey="brand"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
                    className="dark:fill-gray-400"
                  />
                  <PolarRadiusAxis
                    angle={90}
                    domain={[0, 100]}
                    tick={{ fill: '#6b7280', fontSize: 10 }}
                    className="dark:fill-gray-400"
                  />
                  <Radar
                    name="Rating"
                    dataKey="Rating"
                    stroke="#0ea5e9"
                    fill="#0ea5e9"
                    fillOpacity={0.5}
                  />
                  <Radar
                    name="Trust Score"
                    dataKey="Trust Score"
                    stroke="#10b981"
                    fill="#10b981"
                    fillOpacity={0.5}
                  />
                  <Radar
                    name="Product Count"
                    dataKey="Product Count"
                    stroke="#f59e0b"
                    fill="#f59e0b"
                    fillOpacity={0.4}
                  />
                  <Radar
                    name="Avg Reviews"
                    dataKey="Avg Reviews"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.4}
                  />
                  <Legend
                    wrapperStyle={{ fontSize: '12px' }}
                    iconType="circle"
                  />
                  <Tooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload
                        return (
                          <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
                            <p className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                              {data.fullBrand}
                            </p>
                            <div className="space-y-1 text-sm">
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-gray-600 dark:text-gray-400">Rating:</span>
                                <span className="font-semibold text-blue-600 dark:text-blue-400 flex items-center">
                                  <Star className="w-3 h-3 mr-1 fill-current text-yellow-500" />
                                  {data.actualRating}
                                </span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-gray-600 dark:text-gray-400">Trust Score:</span>
                                <span className="font-semibold text-green-600 dark:text-green-400">
                                  {data.actualTrust}%
                                </span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-gray-600 dark:text-gray-400">Products:</span>
                                <span className="font-semibold text-orange-600 dark:text-orange-400">
                                  {data.actualProducts}
                                </span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-gray-600 dark:text-gray-400">Avg Reviews:</span>
                                <span className="font-semibold text-purple-600 dark:text-purple-400">
                                  {data.actualReviews}
                                </span>
                              </div>
                            </div>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
              <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <p className="text-xs text-blue-800 dark:text-blue-300">
                  📊 Note: Values are normalized to 0-100 scale for visual comparison. Hover over the chart to see actual values.
                </p>
              </div>
            </div>
          </div>

          {/* Brand Comparison Table */}
          <div className="card">
            <div className="card-header">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Complete Brand Analysis
              </h3>
            </div>
            <div className="card-body overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 dark:border-gray-700">
                    <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Rank
                    </th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Brand
                    </th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Products
                    </th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Avg Reviews
                    </th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Rating
                    </th>
                    <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Trust Score
                    </th>
                    <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                      Confidence
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {insights.brands.map((brand, index) => (
                    <tr key={index} className="border-b border-gray-100 dark:border-gray-800">
                      <td className="py-3 px-4 text-gray-900 dark:text-gray-100">
                        #{brand.brand_rank}
                      </td>
                      <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                        {brand.Brand}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                        {brand.product_count}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                        {parseFloat(brand.avg_review_count).toFixed(0)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                        {parseFloat(brand.brand_rating).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                        {parseFloat(brand.trust_score).toFixed(1)}%
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          brand.confidence_level == '1' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                          brand.confidence_level == '2' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                          'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                        }`}>
                          {brand.confidence_level == '1' ? 'High' : brand.confidence_level == '2' ? 'Medium' : 'Low'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Review Analysis Tab */}
      {activeTab === 'reviews' && reviewAnalysis && (
        <>
          <div className="grid grid-cols-1 gap-6">
            {/* Review Summary Cards */}
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  Brand Review Analysis
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Sentiment analysis and attribute ratings for each brand
                </p>
              </div>
              <div className="card-body overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Brand
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Reviews
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Sentiment
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Taste
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Quality
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Price
                      </th>
                      <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                        Packaging
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {reviewAnalysis.reviews.map((review, index) => (
                      <tr key={index} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                        <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                          {review.name}
                        </td>
                        <td className="py-3 px-4 text-center text-gray-600 dark:text-gray-400">
                          {review.review_count}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            review.overall_sentiment === 'positive' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                            review.overall_sentiment === 'mixed' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                            'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          }`}>
                            {review.overall_sentiment || 'N/A'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center">
                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${(parseFloat(review.taste || 0) * 100)}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
                              {review.taste ? (parseFloat(review.taste) * 100).toFixed(0) : 'N/A'}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center">
                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-green-600 h-2 rounded-full"
                                style={{ width: `${(parseFloat(review.quality || 0) * 100)}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
                              {review.quality ? (parseFloat(review.quality) * 100).toFixed(0) : 'N/A'}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center">
                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-yellow-600 h-2 rounded-full"
                                style={{ width: `${(parseFloat(review.price || 0) * 100)}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
                              {review.price ? (parseFloat(review.price) * 100).toFixed(0) : 'N/A'}
                            </span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-center">
                          <div className="flex items-center justify-center">
                            <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                              <div
                                className="bg-purple-600 h-2 rounded-full"
                                style={{ width: `${(parseFloat(review.packaging || 0) * 100)}%` }}
                              ></div>
                            </div>
                            <span className="ml-2 text-xs text-gray-600 dark:text-gray-400">
                              {review.packaging ? (parseFloat(review.packaging) * 100).toFixed(0) : 'N/A'}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Review Summaries */}
            <div className="grid grid-cols-1 gap-4">
              {reviewAnalysis.reviews.slice(0, 5).map((review, index) => (
                <div key={index} className="card p-4">
                  <div className="flex items-start justify-between mb-2">
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">{review.name}</h4>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      review.overall_sentiment === 'positive' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                      review.overall_sentiment === 'mixed' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                      'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    }`}>
                      {review.overall_sentiment}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {review.summary}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {/* Product Details Tab */}
      {activeTab === 'products' && silverData && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Product Details
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Showing {insights.products.length} of {silverData.total_products} products
            </p>
          </div>
          <div className="card-body overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Brand
                  </th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Product Name
                  </th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Price
                  </th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Rating
                  </th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Reviews
                  </th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-900 dark:text-gray-100">
                    Price Segment
                  </th>
                </tr>
              </thead>
              <tbody>
                {insights.products.map((product, index) => (
                  <tr key={index} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-gray-100">
                      {product.Brand}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-gray-400 max-w-xs truncate">
                      {product["Product Name"]}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-900 dark:text-gray-100">
                      ₹{parseFloat(product.current_price).toFixed(0)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end">
                        <Star className="w-4 h-4 text-yellow-500 mr-1 fill-current" />
                        <span className="text-gray-900 dark:text-gray-100">
                          {parseFloat(product.Rating).toFixed(1)}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right text-gray-600 dark:text-gray-400">
                      {parseFloat(product.review_count).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-1 text-xs rounded-full ${
                        product.price_segment === 'Luxury' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                        product.price_segment === 'Premium' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                        product.price_segment === 'Mid-Range' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                      }`}>
                        {product.price_segment || 'N/A'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default SearchInsights
