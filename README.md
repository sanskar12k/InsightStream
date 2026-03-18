# InsightStream

> Transform e-commerce product reviews into actionable insights using AI-powered analysis

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## What is InsightStream?

InsightStream is an intelligent e-commerce analytics platform that scrapes product data and reviews from major e-commerce websites, then leverages **AI-powered sentiment analysis** to deliver deep insights into customer opinions. Built for data analysts, market researchers, and business intelligence teams who need to understand market trends at scale.

### Why InsightStream?

- **AI-Driven Analysis**: Powered by Claude AI to extract sentiment, quality ratings, and aspect-specific insights from thousands of reviews
- **Smart Ranking**: Implements Bayesian averaging for more accurate product and brand rankings
- **Interactive Dashboard**: Beautiful React-based UI with real-time data visualization
- **Cloud-Native Storage**: Leverages Cloudflare R2 for scalable, cost-effective data storage

---

## Features

| Feature | Description |
|---------|-------------|
| **Intelligent Scraping** | Automated data collection from e-commerce platforms with rate limiting and error handling |
| **AI Review Analysis** | Multi-dimensional sentiment analysis (taste, quality, price, packaging) using Claude API |
| **Brand Intelligence** | Bayesian-ranked brand analysis with confidence scores and trust metrics |
| **Product Scoring** | Weighted rating system that factors in review count and quality |
| **Price Segmentation** | Automatic categorization into Budget, Mid-Range, Premium, and Luxury segments |
| **OAuth Authentication** | Secure Google OAuth 2.0 integration for user management |
| **Search History** | Track and revisit previous searches with cached results |
| **Export & Share** | Download analysis results in CSV format |

---

## Tech Stack

### Backend
- **FastAPI**: High-performance async API framework
- **MySQL**: Relational database for user data and search history
- **Cloudflare R2**: Object storage for scraped data and analysis results
- **python-dotenv**: Environment configuration management

### Frontend
- **React 18**: Modern UI library with hooks
- **Vite**: Lightning-fast build tool
- **TailwindCSS**: Utility-first styling
- **Recharts**: Interactive data visualizations
- **React Query**: Server state management
- **Axios**: HTTP client

### AI & ML
- **Anthropic Claude API**: Advanced language model for review summarization
- **Bayesian Statistics**: For robust product/brand ranking

---

## Architecture Overview

```
┌─────────────────┐
│   Frontend      │  React + Vite
│   (Port 3000)   │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Backend API   │  FastAPI
│   (Port 8000)   │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬────────────┐
    ↓         ↓          ↓            ↓
┌────────┐ ┌─────┐  ┌────────┐  ┌──────────┐
│ MySQL  │ │ R2  │  │ PySpark│  │ Claude   │
│   DB   │ │Store│  │Pipeline│  │   AI     │
└────────┘ └─────┘  └────────┘  └──────────┘
```

---

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download](https://www.python.org/downloads/)
- **Node.js 16+** - [Download](https://nodejs.org/)
- **MySQL 8.0+** - [Download](https://dev.mysql.com/downloads/)
- **Git** - [Download](https://git-scm.com/)

### 1. Clone the Repository

```bash
git clone https://github.com/sanskar12k/InsightStream.git
cd InsightStream
```

### 2. Backend Setup

#### Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

#### Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cd backend
touch .env
```

Add the following configuration (replace with your actual credentials):

```env
# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_REDIRECT_URI="http://localhost:8000/auth/google/callback"
FRONTEND_URL="http://localhost:3000"
SESSION_SECRET_KEY="generate-a-secure-random-key"

# MySQL Database
MYSQLHOST="localhost"
MYSQLPORT="3306"
MYSQLUSER="your-mysql-user"
MYSQLPASSWORD="your-mysql-password"
MYSQL_DATABASE="insight_stream"

# Cloudflare R2 Storage
R2_ACCESS_KEY_ID="your-r2-access-key"
R2_SECRET_ACCESS_KEY="your-r2-secret-key"
R2_BUCKET_NAME="your-bucket-name"
R2_ENDPOINT_URL="your-r2-endpoint-url"

# Anthropic API
ANTHROPIC_API_KEY="your-anthropic-api-key"
```

#### Database Setup

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE insight_stream;

# Exit MySQL
exit;
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 4. Start the Application

#### Option A: Use the Start Script (Recommended)

```bash
# From project root
chmod +x start-dev.sh
./start-dev.sh
```

This will start both backend and frontend concurrently.

#### Option B: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

## Usage Guide

### 1. Authentication

- Navigate to `http://localhost:3000`
- Click "Sign in with Google"
- Authorize the application

### 2. Search Products

- Enter a product name or category (e.g., "green tea", "coffee beans")
- Click "Search" to start scraping and analysis
- Wait for the data pipeline to complete (this may take a few minutes for large datasets)

### 3. View Insights

The dashboard displays:
- **Product Rankings**: Sorted by weighted ratings
- **Brand Analysis**: Top brands with confidence scores
- **Review Sentiment**: AI-generated summaries with aspect ratings
- **Price Segments**: Distribution across budget categories
- **Quality Metrics**: Taste, packaging, value for money scores

### 4. Export Results

- Click "Export CSV" to download the complete analysis
- Share insights with your team or import into BI tools

---

## API Documentation

Once the backend is running, access the interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scrape` | Initiate product scraping |
| `GET` | `/search/{search_id}` | Get search results by ID |
| `GET` | `/user/searches` | List user's search history |
| `POST` | `/auth/google` | Google OAuth login |
| `GET` | `/health` | Health check |

---

## Project Structure

```
InsightStream/
├── backend/
│   ├── auth/              # Authentication logic
│   ├── database/          # Database models and connections
│   ├── storage/           # R2 storage utilities
│   ├── routes/            # API endpoints
│   ├── .env              # Environment variables (not in git)
│   └── main.py           # FastAPI application entry
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── services/     # API services
│   │   └── App.jsx       # Root component
│   ├── public/           # Static assets
│   └── package.json
│
├── data_pipeline/
│   ├── review_analyze.py  # PySpark analysis pipeline
│   └── ReviewAnalyzer.py  # Claude AI integration
│
├── scrapping/
│   └── scraper.py        # Web scraping logic
│
├── .gitignore
├── start-dev.sh          # Development startup script
└── README.md
```

---

## Configuration Tips

### Generate Session Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
6. Copy Client ID and Client Secret to `.env`

### Cloudflare R2 Setup

1. Sign up at [Cloudflare](https://www.cloudflare.com/)
2. Navigate to R2 Object Storage
3. Create a new bucket
4. Generate API tokens
5. Add credentials to `.env`

### Anthropic API Key

1. Sign up at [Anthropic](https://console.anthropic.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Add to `.env` as `ANTHROPIC_API_KEY`

---

## Performance Optimization

### Spark Configuration

For large datasets, adjust Spark settings in `data_pipeline/review_analyze.py`:

```python
spark = SparkSession.builder \
    .appName("InsightStream") \
    .config("spark.driver.memory", "4g") \
    .config("spark.executor.memory", "4g") \
    .getOrCreate()
```

### Database Indexing

Recommended indexes for MySQL:

```sql
CREATE INDEX idx_user_id ON searches(user_id);
CREATE INDEX idx_created_at ON searches(created_at);
CREATE INDEX idx_search_query ON searches(search_query);
```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'pyspark'`
```bash
# Solution: Ensure virtual environment is activated
source venv/bin/activate
pip install -r backend/requirements.txt
```

**Issue**: `MySQL Connection Error`
```bash
# Solution: Verify MySQL is running
sudo service mysql status
# Check credentials in .env file
```

**Issue**: `R2 Upload Failed`
```bash
# Solution: Verify R2 credentials and bucket permissions
# Check endpoint URL format
```

**Issue**: Frontend can't connect to backend
```bash
# Solution: Ensure backend is running on port 8000
# Check CORS settings in backend/main.py
```

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React code
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

---

## Roadmap

- [ ] Multi-platform scraping support (Amazon, Flipkart, etc.)
- [ ] Real-time scraping with WebSocket updates
- [ ] Advanced filtering and search capabilities
- [ ] Competitive analysis dashboard
- [ ] Email alerts for price drops
- [ ] Mobile app (React Native)
- [ ] Multi-language support
- [ ] Custom AI model fine-tuning

---

## Acknowledgments

- **Anthropic** for the powerful Claude API
- **Apache Spark** for distributed computing capabilities
- **Cloudflare** for R2 object storage
- **Recharts** for beautiful data visualizations

---

## Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/sanskar12k/InsightStream/issues)
- **Email**: sanskar.iitkgp@gmail.com

---

<div align="center">
  <strong>Built with passion for data-driven decision making</strong>
  <br>
  <sub>Made by the InsightStream Team</sub>
</div>
