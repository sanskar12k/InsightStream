# E-Commerce Scraper Frontend

A modern, interactive React application for e-commerce market intelligence and product scraping.

## Features

- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Multi-page Application**: Landing, Login, Register, Dashboard, Searches, Search Detail, Profile
- **Real-time Updates**: Auto-refresh for search status with progress tracking
- **Data Visualization**: Interactive charts and insights using Recharts
- **Authentication**: JWT-based authentication with protected routes
- **Search Management**: Create, track, and analyze product searches
- **Analytics Dashboard**: Brand-level and product-level insights

## Tech Stack

- **React 18** - UI library
- **React Router** - Client-side routing
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client
- **React Query** - Data fetching and caching
- **Recharts** - Data visualization
- **Vite** - Build tool and dev server
- **Lucide React** - Icon library
- **React Hot Toast** - Toast notifications
- **Date-fns** - Date formatting

## Prerequisites

- Node.js 16+ and npm
- Backend API running on http://localhost:8000

## Installation

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Update environment variables** in `.env`:
   ```
   VITE_API_BASE_URL=http://localhost:8000
   VITE_APP_NAME=E-Commerce Scraper
   ```

## Development

Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000

## Build for Production

```bash
npm run build
```

Build output will be in the `dist` directory.

## Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets
├── src/
│   ├── components/      # Reusable components
│   │   ├── Layout.jsx
│   │   ├── Navbar.jsx
│   │   ├── SearchForm.jsx
│   │   └── SearchInsights.jsx
│   ├── contexts/        # React contexts
│   │   └── AuthContext.jsx
│   ├── hooks/           # Custom hooks
│   │   └── useSearch.js
│   ├── pages/           # Page components
│   │   ├── LandingPage.jsx
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── SearchesPage.jsx
│   │   ├── SearchDetailPage.jsx
│   │   └── ProfilePage.jsx
│   ├── services/        # API services
│   │   └── api.js
│   ├── utils/           # Utility functions
│   │   └── formatters.js
│   ├── App.jsx          # Main app component
│   ├── main.jsx         # Entry point
│   └── index.css        # Global styles
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Available Pages

### Public Pages
- **/** - Landing page with features and call-to-action
- **/login** - User login
- **/register** - User registration

### Protected Pages (Require Authentication)
- **/dashboard** - Main dashboard with stats and quick actions
- **/searches** - List of all user searches with filters
- **/search/:id** - Detailed view of a specific search with insights
- **/profile** - User profile and settings

## API Integration

The frontend integrates with the following backend endpoints:

### Authentication
- `POST /users/register` - User registration
- `POST /users/login` - User login
- `GET /users/me` - Get current user
- `PUT /users/password` - Update password
- `DELETE /users/me` - Delete account

### Scraper
- `POST /scrapper/initiate_scrapping` - Start a new search
- `GET /scrapper/search/:id` - Get search status
- `GET /scrapper/my_searches` - Get all user searches

## Features Overview

### 1. Authentication
- Email/password login and registration
- JWT token-based authentication
- Auto-logout on token expiration
- Protected routes

### 2. Dashboard
- Quick stats (total searches, completed, in progress, failed)
- Recent searches
- Quick action cards

### 3. Search Management
- Create new product searches
- Configure search parameters:
  - Product name
  - Platform (Amazon, Flipkart)
  - Category
  - Max products
  - Deep details
  - Include reviews
- Real-time progress tracking
- Auto-refresh for in-progress searches

### 4. Search Insights
- Overview tab with summary stats
- Brand analysis with charts
- Pricing insights
- Rating distribution
- Top products list

### 5. Profile Management
- View account information
- Change password
- Delete account

## Customization

### Updating Colors

Edit `tailwind.config.js` to change the primary color scheme:

```javascript
colors: {
  primary: {
    // Your color palette
  },
}
```

### Adding New Features

1. Create new component in `src/components/`
2. Add route in `src/App.jsx`
3. Create API service in `src/services/api.js`
4. Add data fetching hook in `src/hooks/`

## Notes

- **Google OAuth**: Currently not implemented in the backend. The login page has a placeholder for Google OAuth integration.
- **Search Insights**: Currently uses mock data. Update `SearchInsights.jsx` to fetch actual CSV data from the backend.
- **Auto-refresh**: Search detail page auto-refreshes every 5 seconds for in-progress searches.

## Troubleshooting

### CORS Issues
Make sure the backend allows requests from `http://localhost:3000`. Check `backend/config.py`:

```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

### API Connection
Verify the backend is running on `http://localhost:8000` and the `.env` file has the correct API URL.

### Build Errors
Clear node_modules and reinstall:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Future Enhancements

- [ ] Google OAuth integration
- [ ] Real-time WebSocket updates
- [ ] Export data to Excel/PDF
- [ ] Comparison view for multiple searches
- [ ] Dark mode support
- [ ] Email notifications
- [ ] Advanced filtering and sorting
- [ ] Saved search templates

## License

MIT
