# Quick Start Guide

## ✅ All Dependencies Installed!

Everything is now ready to run. Here's what was installed:

### Backend Dependencies ✅
- Python 3.9.6 (in virtual environment)
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PyMySQL 1.1.0
- JWT authentication libraries
- All other backend packages

### Frontend Dependencies ✅
- Node.js v25.8.0
- npm v11.11.0
- React 18.3.1
- Vite 5.4.21
- 382 npm packages total

### Database ✅
- MySQL is running (process ID: 41070)

---

## 🚀 How to Run the Application

### Option 1: Quick Start Script (Recommended)

```bash
cd /Users/mw-sanskar/Documents/sanskar/projects/EcommerceScrapper
./start-dev.sh
```

This will start both backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd /Users/mw-sanskar/Documents/sanskar/projects/EcommerceScrapper
source venv/bin/activate  # Activate virtual environment
python app.py
```

**Terminal 2 - Frontend:**
```bash
cd /Users/mw-sanskar/Documents/sanskar/projects/EcommerceScrapper/frontend
npm run dev
```

---

## 🌐 Access URLs

Once running, access the application at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)

---

## 📝 First Steps

1. **Open your browser** to http://localhost:3000

2. **Create an account**:
   - Click "Get Started" or "Register"
   - Fill in:
     - Name (3-50 characters)
     - Email (valid email)
     - Password (min 6 characters)
   - Click "Create Account"

3. **Create your first search**:
   - From the dashboard, click "New Search"
   - Enter product name (e.g., "iPhone 15 Pro")
   - Select platform (Amazon)
   - Set max products (default: 80)
   - Click "Start Search"

4. **Monitor progress**:
   - You'll be redirected to the search detail page
   - Watch real-time progress updates
   - Page auto-refreshes every 5 seconds

5. **View insights**:
   - Once completed, view analytics and charts
   - Explore brand analysis, pricing, ratings

---

## 🛠️ Development Commands

### Frontend

```bash
cd frontend

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint
```

### Backend

```bash
# Activate virtual environment
source venv/bin/activate

# Run server
python app.py

# Check database connection
python debug.py
```

---

## 📊 Application Features

### ✅ Available Now
- User registration and login
- JWT authentication
- Create product searches
- Real-time progress tracking
- Search history
- Interactive analytics dashboard
- Brand analysis
- Pricing insights
- Rating distribution
- Profile management
- Password updates

### 🔄 Coming Soon
- Google OAuth login
- Real-time WebSocket updates
- CSV data export
- Email notifications
- Scheduled searches

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Make sure MySQL is running
brew services list | grep mysql

# Check if port 8000 is available
lsof -ti:8000 | xargs kill -9  # Kill any process on port 8000

# Verify database connection
mysql -u insight_stream_backend -p -h localhost ecommerce_research
```

### Frontend won't start
```bash
# Make sure port 3000 is available
lsof -ti:3000 | xargs kill -9  # Kill any process on port 3000

# Clear and reinstall if needed
rm -rf node_modules package-lock.json
npm install
```

### CORS errors
Make sure `backend/config.py` includes:
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

---

## 📁 Important Files

- `app.py` - Backend entry point
- `frontend/src/main.jsx` - Frontend entry point
- `backend/config.py` - CORS and backend config
- `frontend/.env` - Frontend environment variables
- `SETUP_GUIDE.md` - Detailed setup instructions
- `PROJECT_OVERVIEW.md` - Complete project documentation

---

## 🎯 Key Features

### Authentication
- Secure JWT-based authentication
- Token expires after 24 hours
- Password hashing with bcrypt

### Search Configuration
- Product name (required)
- Platform selection (Amazon, Flipkart)
- Optional category
- Max products (1-500)
- Deep details toggle
- Include reviews option

### Analytics
- Overview with summary stats
- Brand distribution charts
- Price distribution graphs
- Rating analysis
- Top products ranking

---

## 💡 Tips

1. **Development**: Use the quick start script for easy development
2. **Testing**: Create a test search with max_products=10 for faster results
3. **Debugging**: Check browser console and backend logs for errors
4. **Database**: Use MySQL Workbench or phpMyAdmin for database management

---

## 📞 Need Help?

- Check `SETUP_GUIDE.md` for detailed instructions
- Review `PROJECT_OVERVIEW.md` for architecture details
- Check application logs for errors
- Review API documentation at http://localhost:8000/docs

---

**Everything is ready! Run `./start-dev.sh` to begin!** 🚀
