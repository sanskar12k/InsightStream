import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const LoginPage = () => {
  const navigate = useNavigate()

  // Redirect to home page (landing page has the login button)
  useEffect(() => {
    navigate('/', { replace: true })
  }, [navigate])

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center px-4 py-12">
      <div className="text-center">
        <p className="text-gray-600 dark:text-gray-400">Redirecting to home...</p>
      </div>
    </div>
  )
}

export default LoginPage
