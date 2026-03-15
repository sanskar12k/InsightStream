import { format, formatDistanceToNow } from 'date-fns'

export const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm')
  } catch (error) {
    return dateString
  }
}

export const formatRelativeTime = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return formatDistanceToNow(new Date(dateString), { addSuffix: true })
  } catch (error) {
    return dateString
  }
}

export const formatCurrency = (amount, currency = 'INR') => {
  if (amount === null || amount === undefined) return 'N/A'

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

export const formatNumber = (number) => {
  if (number === null || number === undefined) return 'N/A'

  return new Intl.NumberFormat('en-IN').format(number)
}

export const getStatusColor = (status) => {
  const colors = {
    PENDING: 'badge-info',
    IN_PROGRESS: 'badge-warning',
    COMPLETED: 'badge-success',
    FAILED: 'badge-error',
  }
  return colors[status] || 'badge-info'
}

export const getStatusText = (status) => {
  const texts = {
    PENDING: 'Pending',
    IN_PROGRESS: 'In Progress',
    COMPLETED: 'Completed',
    FAILED: 'Failed',
  }
  return texts[status] || status
}

export const truncateText = (text, maxLength = 50) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}

export const calculateDiscount = (mrp, currentPrice) => {
  if (!mrp || !currentPrice || mrp <= currentPrice) return 0
  return Math.round(((mrp - currentPrice) / mrp) * 100)
}
