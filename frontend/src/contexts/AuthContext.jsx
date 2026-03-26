import { createContext, useContext, useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token')
      const storedUser = localStorage.getItem('user')

      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser))
          // Optionally verify token with backend
          const response = await authAPI.getCurrentUser()
          setUser(response.data)
          localStorage.setItem('user', JSON.stringify(response.data))
        } catch (error) {
          console.error('Token verification failed:', error)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setUser(null)
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [])

  const login = async (email, password) => {
    try {
      // Clear all cached data before login to prevent data leakage
      queryClient.clear()
      const response = await authAPI.login({ email, password })
      const { access_token, user: userData } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)

      toast.success('Login successful!')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const register = async (name, email, password) => {
    try {
      // Clear all cached data before registration
      queryClient.clear()

      const response = await authAPI.register({ name, email, password })
      const { access_token, user: userData } = response.data

      localStorage.setItem('token', access_token)
      localStorage.setItem('user', JSON.stringify(userData))
      setUser(userData)

      toast.success('Registration successful!')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Registration failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const logout = () => {
    // Clear all React Query cache to prevent data leakage
    queryClient.clear()

    // Clear localStorage
    localStorage.removeItem('token')
    localStorage.removeItem('user')

    // Clear user state
    setUser(null)

    toast.success('Logged out successfully')
  }

  const updatePassword = async (oldPassword, newPassword) => {
    try {
      await authAPI.updatePassword({
        old_password: oldPassword,
        new_password: newPassword,
      })
      toast.success('Password updated successfully')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Password update failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const deleteAccount = async () => {
    try {
      await authAPI.deleteAccount()

      // Clear all React Query cache
      queryClient.clear()

      localStorage.removeItem('token')
      localStorage.removeItem('user')
      setUser(null)
      toast.success('Account deleted successfully')
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Account deletion failed'
      toast.error(message)
      return { success: false, error: message }
    }
  }

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    updatePassword,
    deleteAccount,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
