import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  register: (data) => api.post('/users/register', data),
  login: (data) => api.post('/users/login', data),
  getCurrentUser: () => api.get('/users/me'),
  updatePassword: (data) => api.put('/users/password', data),
  deleteAccount: () => api.delete('/users/me'),
}

// Scraper API
export const scraperAPI = {
  initiateSearch: (data) => api.post('/scrapper/initiate_scrapping', data),
  getSearchStatus: (searchId) => api.get(`/scrapper/search/${searchId}`),
  getMySearches: (params) => api.get('/scrapper/my_searches', { params }),
  getSearchStatistics: () => api.get('/scrapper/search_statistics'),
  getCsvPreview: (searchId) => api.get(`/scrapper/csv_preview/${searchId}`),
  downloadCsv: (searchId) => api.get(`/scrapper/download_csv/${searchId}`, { responseType: 'blob' }),
  getBrandInsights: (searchId) => api.get(`/scrapper/brand_insights/${searchId}`),
  getReviewAnalysis: (searchId) => api.get(`/scrapper/review_analysis/${searchId}`),
  getSilverData: (searchId, params) => api.get(`/scrapper/silver_data/${searchId}`, { params }),
  generateInsights: (searchId) => api.post(`/scrapper/generate_insights/${searchId}`),
}

// Export default api instance for custom requests
export default api
