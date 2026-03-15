import { useState } from 'react'
import { X, Search } from 'lucide-react'

const SearchForm = ({ onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    product_name: '',
    platform: ['amazon'],
    category: '',
    deep_details: true,
    max_products: 80,
    include_reviews: false,
    auto_generate_insights: false,
  })
  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }))
    }
  }

  const handlePlatformChange = (platform) => {
    setFormData((prev) => {
      const platforms = prev.platform.includes(platform)
        ? prev.platform.filter((p) => p !== platform)
        : [...prev.platform, platform]
      return { ...prev, platform: platforms }
    })
  }

  const validateForm = () => {
    const newErrors = {}

    if (!formData.product_name || formData.product_name.trim().length < 2) {
      newErrors.product_name = 'Product name must be at least 2 characters'
    } else if (formData.product_name.length > 100) {
      newErrors.product_name = 'Product name must be less than 100 characters'
    }

    if (formData.platform.length === 0) {
      newErrors.platform = 'Select at least one platform'
    }

    const maxProducts = parseInt(formData.max_products)
    if (isNaN(maxProducts) || maxProducts < 1 || maxProducts > 500) {
      newErrors.max_products = 'Max products must be between 1 and 500'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    if (!validateForm()) return

    onSubmit({
      ...formData,
      max_products: parseInt(formData.max_products),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl rounded-3xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200 dark:border-gray-700 animate-slide-up">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-primary-50 to-purple-50 dark:from-primary-900/30 dark:to-purple-900/30 border-b border-gray-200 dark:border-gray-700 px-6 py-5 flex items-center justify-between rounded-t-3xl backdrop-blur-xl">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">New Product Search</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/80 rounded-xl transition-all duration-300 hover:scale-110 hover:rotate-90 group"
          >
            <X className="w-6 h-6 text-gray-500 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Product Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Product Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="product_name"
              value={formData.product_name}
              onChange={handleChange}
              className={`input-field ${errors.product_name ? 'border-red-500' : ''}`}
              placeholder="e.g., iPhone 15 Pro"
            />
            {errors.product_name && (
              <p className="mt-1 text-sm text-red-600">{errors.product_name}</p>
            )}
          </div>

          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Platform <span className="text-red-500">*</span>
            </label>
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                <input
                  type="checkbox"
                  checked={formData.platform.includes('amazon')}
                  onChange={() => handlePlatformChange('amazon')}
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Amazon</span>
              </label>
              <label className="flex items-center space-x-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 opacity-50">
                <input
                  type="checkbox"
                  checked={formData.platform.includes('flipkart')}
                  onChange={() => handlePlatformChange('flipkart')}
                  disabled
                  className="w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Flipkart (Coming Soon)
                </span>
              </label>
            </div>
            {errors.platform && (
              <p className="mt-1 text-sm text-red-600">{errors.platform}</p>
            )}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Category (Optional)
            </label>
            <input
              type="text"
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g., Electronics, Grocery"
            />
          </div>

          {/* Max Products */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Maximum Products
            </label>
            <input
              type="number"
              name="max_products"
              value={formData.max_products}
              onChange={handleChange}
              min="1"
              max="500"
              className={`input-field ${errors.max_products ? 'border-red-500' : ''}`}
            />
            {errors.max_products && (
              <p className="mt-1 text-sm text-red-600">{errors.max_products}</p>
            )}
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Number of products to scrape (1-500)
            </p>
          </div>

          {/* Advanced Options */}
          <div className="space-y-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">Advanced Options</h3>

            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="deep_details"
                checked={formData.deep_details}
                onChange={handleChange}
                className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Include Deep Details
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Scrape additional product information (weight, dimensions, manufacturer, etc.)
                </p>
              </div>
            </label>

            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="include_reviews"
                checked={formData.include_reviews}
                onChange={handleChange}
                className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Include Customer Reviews
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Scrape customer reviews and ratings (may increase processing time)
                </p>
              </div>
            </label>

            <label className="flex items-start space-x-3 cursor-pointer">
              <input
                type="checkbox"
                name="auto_generate_insights"
                checked={formData.auto_generate_insights}
                onChange={handleChange}
                className="mt-1 w-4 h-4 text-primary-600 rounded focus:ring-primary-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Auto-Generate Insights
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Automatically generate brand insights and review analysis after scraping completes
                </p>
              </div>
            </label>
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 btn-primary shadow-xl"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  Initiating...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <Search className="w-5 h-5" />
                  Start Search
                </span>
              )}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-8 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-xl font-semibold hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-500 hover:scale-105 transition-all duration-300 active:scale-95 shadow-md"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default SearchForm
