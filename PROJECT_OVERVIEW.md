# E-Commerce Scraper - Project Overview

## 📋 Table of Contents
- [Introduction](#introduction)
- [Architecture](#architecture)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Frontend Pages](#frontend-pages)

## 🎯 Introduction

E-Commerce Scraper is a full-stack web application designed for market intelligence and competitive analysis. It allows users to scrape product data from multiple e-commerce platforms, analyze pricing trends, compare brands, and gain valuable insights.

## 🏗️ Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌──────────────────┐
│                 │         │                 │         │                  │
│  React Frontend │ ──────► │  FastAPI Backend│ ──────► │  MySQL Database  │
│  (Port 3000)    │ ◄────── │  (Port 8000)    │ ◄────── │  (Port 3306)     │
│                 │  HTTP   │                 │  SQL    │                  │
└─────────────────┘  REST   └─────────────────┘         └──────────────────┘
                                     │
                                     │
                                     ▼
                            ┌─────────────────┐
                            │                 │
                            │ Scraping Engine │
                            │  (Selenium)     │
                            │                 │
                            └─────────────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
                            │   CSV Files     │
                            │  (scrape_results)│
                            └─────────────────┘
```

## ✨ Features

### User Management
- ✅ User registration and authentication
- ✅ JWT-based secure sessions
- ✅ Profile management
- ✅ Password updates
- ✅ Account deletion
- 🔄 Google OAuth (planned)

### Search Management
- ✅ Create product searches
- ✅ Multi-platform support (Amazon, Flipkart)
- ✅ Configurable search parameters
- ✅ Real-time progress tracking
- ✅ Search history
- ✅ Status monitoring

### Data Analytics
- ✅ Brand-level insights
- ✅ Product-level analysis
- ✅ Price distribution charts
- ✅ Rating analytics
- ✅ Interactive visualizations
- ✅ Top products ranking

### Additional Features
- ✅ Responsive design
- ✅ Auto-refresh for active searches
- ✅ Toast notifications
- ✅ Error handling
- ✅ Clean UI/UX

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| Python 3.8+ | Programming language |
| FastAPI 0.104.1 | Web framework |
| SQLAlchemy 2.0.23 | ORM |
| MySQL | Database |
| JWT | Authentication |
| Selenium | Web scraping |
| Pandas | Data processing |
| PySpark | Big data processing |
| Uvicorn | ASGI server |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18.2 | UI library |
| Vite 5.0 | Build tool |
| React Router 6.21 | Routing |
| Tailwind CSS 3.3 | Styling |
| Axios 1.6 | HTTP client |
| React Query 5.14 | Data fetching |
| Recharts 2.10 | Charts |
| Lucide React | Icons |
| Date-fns 3.0 | Date formatting |

## 📁 Project Structure

```
EcommerceScrapper/
│
├── 📄 app.py                          # Backend entry point
├── 📄 SETUP_GUIDE.md                  # Complete setup instructions
├── 📄 PROJECT_OVERVIEW.md             # This file
├── 📄 start-dev.sh                    # Quick start script
│
├── 📁 backend/                        # Backend code
│   ├── 📄 config.py                   # CORS & settings
│   ├── 📄 requirement.txt             # Python dependencies
│   │
│   ├── 📁 api/routes/
│   │   ├── 📄 user.py                 # User endpoints
│   │   └── 📄 scrapper.py             # Scraper endpoints
│   │
│   ├── 📁 auth/
│   │   └── 📄 jwt_auth.py             # JWT authentication
│   │
│   ├── 📁 database/
│   │   └── 📄 database.py             # DB connection
│   │
│   ├── 📁 models/
│   │   ├── 📄 user_models.py          # User schemas
│   │   ├── 📄 db_models.py            # DB models
│   │   └── 📄 scrapper_models.py      # Scraper schemas
│   │
│   └── 📁 services/
│       └── 📄 db_services.py          # DB operations
│
├── 📁 scrapping/                      # Web scraping
│   ├── 📄 ecommerce_scraper_backend.py
│   ├── 📄 Amazon_Scrapper.py
│   ├── 📄 Flipkart_Scrapper.py
│   └── ...
│
├── 📁 frontend/                       # Frontend code
│   ├── 📄 package.json                # Node dependencies
│   ├── 📄 vite.config.js              # Vite config
│   ├── 📄 tailwind.config.js          # Tailwind config
│   ├── 📄 index.html                  # HTML template
│   ├── 📄 README.md                   # Frontend docs
│   │
│   ├── 📁 public/                     # Static assets
│   │
│   └── 📁 src/
│       ├── 📄 main.jsx                # Entry point
│       ├── 📄 App.jsx                 # Main component
│       ├── 📄 index.css               # Global styles
│       │
│       ├── 📁 components/             # React components
│       │   ├── 📄 Layout.jsx
│       │   ├── 📄 Navbar.jsx
│       │   ├── 📄 SearchForm.jsx
│       │   └── 📄 SearchInsights.jsx
│       │
│       ├── 📁 pages/                  # Page components
│       │   ├── 📄 LandingPage.jsx
│       │   ├── 📄 LoginPage.jsx
│       │   ├── 📄 RegisterPage.jsx
│       │   ├── 📄 DashboardPage.jsx
│       │   ├── 📄 SearchesPage.jsx
│       │   ├── 📄 SearchDetailPage.jsx
│       │   └── 📄 ProfilePage.jsx
│       │
│       ├── 📁 contexts/               # React contexts
│       │   └── 📄 AuthContext.jsx
│       │
│       ├── 📁 hooks/                  # Custom hooks
│       │   └── 📄 useSearch.js
│       │
│       ├── 📁 services/               # API services
│       │   └── 📄 api.js
│       │
│       └── 📁 utils/                  # Utilities
│           └── 📄 formatters.js
│
└── 📁 scrape_results/                 # CSV output files
```

## 🚀 Getting Started

### Quick Start

```bash
# 1. Start MySQL database
sudo systemctl start mysql

# 2. Run the development script
./start-dev.sh
```

### Manual Start

**Backend:**
```bash
python app.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 API Documentation

### Authentication Endpoints

#### Register
```http
POST /users/register
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123"
}
```

#### Login
```http
POST /users/login
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "password123"
}
```

#### Get Current User
```http
GET /users/me
Authorization: Bearer <token>
```

### Scraper Endpoints

#### Initiate Search
```http
POST /scrapper/initiate_scrapping
Authorization: Bearer <token>
Content-Type: application/json

{
  "product_name": "iPhone 15 Pro",
  "platform": ["amazon"],
  "category": "Electronics",
  "max_products": 80,
  "deep_details": true,
  "include_reviews": false
}
```

#### Get Search Status
```http
GET /scrapper/search/{search_id}
Authorization: Bearer <token>
```

#### Get All Searches
```http
GET /scrapper/my_searches
Authorization: Bearer <token>
```

## 🎨 Frontend Pages

### Public Pages

1. **Landing Page** (`/`)
   - Hero section with features
   - Benefits showcase
   - Call-to-action
   - Statistics

2. **Login Page** (`/login`)
   - Email/password login
   - Google OAuth placeholder
   - Form validation

3. **Register Page** (`/register`)
   - User registration
   - Password confirmation
   - Email validation

### Protected Pages

4. **Dashboard** (`/dashboard`)
   - Welcome banner
   - Statistics cards
   - Recent searches
   - Quick actions
   - New search button

5. **Searches Page** (`/searches`)
   - All user searches
   - Filters (status, search query)
   - Search cards with details
   - Progress indicators

6. **Search Detail Page** (`/search/:id`)
   - Search information
   - Real-time progress
   - Status updates
   - Insights & analytics
   - Charts and graphs

7. **Profile Page** (`/profile`)
   - User information
   - Change password
   - Account deletion
   - Security settings

## 🎯 Key Features Explained

### 1. Real-time Progress Tracking
- Auto-refresh every 5 seconds for active searches
- Live progress bar
- Status badges (Pending, In Progress, Completed, Failed)

### 2. Interactive Analytics
- **Overview Tab**: Summary statistics, top products
- **Brand Analysis**: Distribution charts, comparison tables
- **Pricing Insights**: Price distribution graphs
- **Ratings**: Rating distribution analysis

### 3. Secure Authentication
- JWT token-based authentication
- Token stored in localStorage
- Auto-logout on expiration
- Protected routes
- Password hashing with bcrypt

### 4. Search Configuration
- Product name (required)
- Platform selection (Amazon, Flipkart)
- Optional category
- Max products (1-500)
- Deep details toggle
- Include reviews option

## 📊 Data Flow

### Creating a Search

```
User → SearchForm → API Request → Backend
                                     ↓
                              Create DB Record
                                     ↓
                              Background Task
                                     ↓
                              Scraping Engine
                                     ↓
                              Save to CSV
                                     ↓
                              Update DB Status
                                     ↓
User ← Status Update ← Auto-refresh ← Database
```

### Authentication Flow

```
User → Login Form → POST /users/login → Backend
                                           ↓
                                    Verify Credentials
                                           ↓
                                    Generate JWT Token
                                           ↓
User ← Token Response ← Store in localStorage
         ↓
    All API Requests
         ↓
    Authorization: Bearer <token>
```

## 🔐 Security Features

- ✅ JWT authentication
- ✅ Password hashing (bcrypt)
- ✅ CORS configuration
- ✅ Input validation
- ✅ SQL injection protection (ORM)
- ✅ XSS protection
- ⚠️ Rate limiting (recommended)
- ⚠️ HTTPS (production)

## 📈 Performance Considerations

### Backend
- Connection pooling (pool_size: 10)
- Background task processing
- Efficient database queries
- Indexed database fields

### Frontend
- React Query caching
- Lazy loading
- Optimized re-renders
- Code splitting with Vite

## 🚧 Known Limitations

1. **Google OAuth**: Not yet implemented (backend support needed)
2. **Flipkart Scraper**: Not fully integrated
3. **Real-time Updates**: Using polling (WebSocket recommended)
4. **CSV Parsing**: Frontend shows mock data for insights
5. **File Download**: Not yet implemented

## 🔮 Future Roadmap

### Phase 1 (Current)
- ✅ Basic authentication
- ✅ Search management
- ✅ Data visualization

### Phase 2 (Next)
- [ ] Google OAuth
- [ ] WebSocket updates
- [ ] CSV data parsing
- [ ] Export functionality

### Phase 3 (Future)
- [ ] Email notifications
- [ ] Scheduled searches
- [ ] Advanced analytics
- [ ] Comparison tools
- [ ] Dark mode
- [ ] Mobile app

## 📝 Development Notes

### Adding New Features

1. **Backend**:
   - Add endpoint in `backend/api/routes/`
   - Add models in `backend/models/`
   - Update database schema if needed

2. **Frontend**:
   - Create component in `src/components/`
   - Add page in `src/pages/`
   - Update routing in `App.jsx`
   - Add API call in `src/services/api.js`

### Code Style

- **Backend**: PEP 8 Python style guide
- **Frontend**: ESLint configuration
- **Commits**: Descriptive commit messages
- **Documentation**: Update docs with changes

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

MIT License - See LICENSE file for details

## 👥 Support

For issues or questions:
- Check SETUP_GUIDE.md
- Review API documentation
- Check application logs
- Open an issue on GitHub

---

**Built with ❤️ using React, FastAPI, and modern web technologies**
