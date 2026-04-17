import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

const OAuthCallbackPage = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleOAuthCallback = async () => {
      try {
        // Extract token and user data from URL params
        const urlParams = new URLSearchParams(window.location.search)
        const token = urlParams.get('token')
        const userDataParam = urlParams.get('user')

        if (token && userDataParam) {
          // Parse user data
          const userData = JSON.parse(decodeURIComponent(userDataParam))

          // Store token and user in localStorage
          localStorage.setItem('token', token)
          localStorage.setItem('user', JSON.stringify(userData))

          toast.success('Successfully signed in with Google!')

          // Force page reload to trigger AuthContext to load user from localStorage
          window.location.href = '/dashboard'
        } else {
          console.error('No token or user data found in URL')
          toast.error('Google sign-in failed. Please try again.')
          navigate('/', { replace: true })
        }
      } catch (error) {
        console.error('OAuth callback error:', error)
        toast.error('Failed to complete sign-in. Please try again.')
        navigate('/', { replace: true })
      }
    }

    handleOAuthCallback()
  }, [navigate])

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
