import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const OAuthCallbackPage = () => {
  const navigate = useNavigate()
  const { setUser, setToken } = useAuth()

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // The backend should send the full response with token
        // We're on the callback URL now after Google redirects
        const currentUrl = window.location.href

        // Check if we're coming from the backend callback
        // The backend returns JSON, so we need to extract it

        // Option 1: If backend redirects with token in URL params
        const urlParams = new URLSearchParams(window.location.search)
        const token = urlParams.get('token')

        if (token) {
          // Parse user data if included
          const userDataParam = urlParams.get('user')
          const userData = userDataParam ? JSON.parse(decodeURIComponent(userDataParam)) : null

          // Store token and user
          localStorage.setItem('token', token)
          if (userData) {
            localStorage.setItem('user', JSON.stringify(userData))
            setUser(userData)
          }
          setToken(token)

          // Redirect to dashboard
          navigate('/dashboard', { replace: true })
        } else {
          // Option 2: Token is in the response body (API returns JSON)
          // This happens when backend endpoint returns JSON directly
          console.error('No token found in URL. Check backend /auth/google/callback response.')
          navigate('/login', { replace: true })
        }
      } catch (error) {
        console.error('OAuth callback error:', error)
        navigate('/login', { replace: true })
      }
    }

    handleOAuthCallback()
  }, [navigate, setUser, setToken])

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          Completing sign in...
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Please wait while we finish setting up your account
        </p>
      </div>
    </div>
  )
}

export default OAuthCallbackPage
