import { Link } from 'react-router-dom'
import { Search, TrendingUp, BarChart3, Shield, Zap, Users } from 'lucide-react'
import ThemeToggle from '../components/ThemeToggle'

const LandingPage = () => {
  const features = [
    {
      icon: <Search className="w-8 h-8" />,
      title: 'Smart Product Search',
      description: 'Search across multiple e-commerce platforms with advanced filters and get comprehensive product data.',
    },
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: 'Deep Analytics',
      description: 'Get detailed insights at brand and product level with pricing trends and market intelligence.',
    },
    {
      icon: <TrendingUp className="w-8 h-8" />,
      title: 'Market Intelligence',
      description: 'Track competitor pricing, ratings, and reviews to make informed business decisions.',
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Real-time Data',
      description: 'Access fresh data with automated scraping and live status updates on your searches.',
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Secure & Reliable',
      description: 'Enterprise-grade security with JWT authentication and encrypted data storage.',
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: 'User-friendly',
      description: 'Intuitive dashboard with organized search history and easy-to-use interface.',
    },
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-primary-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navigation */}
      <nav className="bg-white/90 dark:bg-gray-900/90 backdrop-blur-xl border-b border-gray-200/50 dark:border-gray-700/50 fixed w-full top-0 z-50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2 group cursor-pointer">
              <div className="bg-gradient-to-br from-primary-600 to-purple-600 p-2 rounded-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                <Search className="w-6 h-6 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
                Insight Stream
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <Link to="/login" className="btn-ghost">
                Login
              </Link>
              <Link to="/register" className="btn-primary">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-50 via-purple-50 to-pink-50 opacity-50"></div>
        <div className="absolute top-20 left-10 w-72 h-72 bg-primary-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '1s' }}></div>

        <div className="max-w-7xl mx-auto text-center relative z-10">
          <div className="animate-fade-in">
            <h1 className="text-6xl md:text-7xl font-extrabold text-gray-900 dark:text-gray-100 mb-6 leading-tight">
              Market Intelligence Made
              <span className="bg-gradient-to-r from-primary-600 via-purple-600 to-pink-600 bg-clip-text text-transparent animate-glow"> Simple</span>
            </h1>
            <p className="text-2xl text-gray-700 dark:text-gray-300 mb-10 max-w-3xl mx-auto leading-relaxed">
              Scrape, analyze, and gain insights from multiple e-commerce platforms.
              Make data-driven decisions with our powerful market research platform.
            </p>
            <div className="flex flex-col sm:flex-row gap-6 justify-center">
              <Link to="/register" className="btn-primary text-lg px-10 py-5 text-white shadow-2xl">
                Start Free Trial
              </Link>
              <a href="#features" className="btn-secondary text-lg px-10 py-5">
                Learn More
              </a>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20 animate-slide-up">
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl hover:shadow-primary-500/30 hover:scale-105 transition-all duration-300 border border-gray-100 dark:border-gray-700 group cursor-pointer">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent mb-2 group-hover:scale-110 transition-transform">10K+</div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">Products Scraped</div>
            </div>
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl hover:shadow-purple-500/30 hover:scale-105 transition-all duration-300 border border-gray-100 dark:border-gray-700 group cursor-pointer">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2 group-hover:scale-110 transition-transform">500+</div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">Active Users</div>
            </div>
            <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-xl rounded-2xl p-8 shadow-2xl hover:shadow-green-500/30 hover:scale-105 transition-all duration-300 border border-gray-100 dark:border-gray-700 group cursor-pointer">
              <div className="text-5xl font-extrabold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent mb-2 group-hover:scale-110 transition-transform">99.9%</div>
              <div className="text-gray-700 dark:text-gray-300 font-medium">Uptime</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              Powerful Features for Market Research
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Everything you need to gather and analyze e-commerce data
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="card p-8 group cursor-pointer border-2 border-transparent hover:border-primary-200 dark:hover:border-primary-600"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="text-primary-600 dark:text-primary-400 mb-4 transform group-hover:scale-110 group-hover:rotate-6 transition-all duration-300 inline-block bg-gradient-to-br from-primary-100 to-purple-100 dark:from-primary-900 dark:to-purple-900 p-4 rounded-2xl shadow-lg">
                  {feature.icon}
                </div>
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-primary-600 to-primary-700">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Ready to Get Started?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Join hundreds of businesses using our platform for market intelligence
          </p>
          <Link
            to="/register"
            className="inline-block px-8 py-4 bg-white text-primary-600 rounded-lg font-semibold text-lg hover:bg-gray-100 transition-colors duration-200"
          >
            Create Free Account
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 dark:bg-gray-950 text-gray-300 dark:text-gray-400 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="bg-primary-600 dark:bg-primary-700 p-2 rounded-lg">
              <Search className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-white dark:text-gray-100">Insight Stream</span>
          </div>
          <p className="text-sm">
            © 2024 Insight Stream. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
