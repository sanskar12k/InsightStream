# Changelog - Insight Stream

## Version 2.0.0 - Dark Mode & Rebranding (Latest)

### 🎨 Major Features

#### 1. **Dark Mode Implementation**
- ✅ Automatic system preference detection
- ✅ Manual theme toggle in navbar
- ✅ LocalStorage persistence
- ✅ Smooth transitions between themes
- ✅ Complete coverage across all components
- ✅ Glass-morphism effects in both modes

#### 2. **Platform Rebranding**
- ✅ Name changed from "E-Commerce Scraper" to "Insight Stream"
- ✅ Updated across all pages and components
- ✅ Environment variables updated
- ✅ HTML title and meta tags updated

### 📁 New Files
- `src/contexts/ThemeContext.jsx` - Theme management context
- `src/components/ThemeToggle.jsx` - Theme toggle button component
- `DARK_MODE_GUIDE.md` - Complete dark mode documentation

### 🔧 Modified Files

#### Configuration
- `tailwind.config.js` - Added `darkMode: 'class'`
- `index.html` - Updated title to "Insight Stream"
- `.env` - Updated VITE_APP_NAME
- `.env.example` - Updated VITE_APP_NAME

#### Contexts
- `src/main.jsx` - Added ThemeProvider wrapper
- `src/contexts/AuthContext.jsx` - Added React Query cache clearing

#### Components
- `src/components/Navbar.jsx`
  - Added ThemeToggle component
  - Added dark mode classes
  - Updated branding to "Insight Stream"
  - Enhanced mobile menu with theme toggle

#### Styles
- `src/index.css`
  - Added dark mode support to all base styles
  - Added dark variants for cards, inputs, badges
  - Enhanced transitions for theme switching

#### Pages
- `src/pages/LandingPage.jsx` - Updated branding, added dark mode classes
- `src/pages/LoginPage.jsx` - Updated branding
- `src/pages/RegisterPage.jsx` - Updated branding
- All other pages: Ready for dark mode (inherit global styles)

### 🎨 Visual Improvements

#### Light Mode
- Background: Gradient from gray-50 → blue-50 → purple-50
- Cards: White with 80% opacity, backdrop blur
- Text: Gray-900
- Borders: Gray-200

#### Dark Mode
- Background: Gradient from gray-900 → gray-800 → gray-900
- Cards: Gray-800 with 80% opacity, backdrop blur
- Text: Gray-100
- Borders: Gray-700

### 🔄 Bug Fixes
- Fixed logout/login data persistence issue
- React Query cache now clears on logout
- User data properly isolated between sessions

### 🚀 Performance
- Theme applied before first render (no FOUC)
- Smooth 300ms CSS transitions
- GPU-accelerated transforms
- Efficient localStorage usage

### 📱 Browser Support
- Chrome 76+
- Firefox 67+
- Safari 12.1+
- Edge 79+
- System preference detection in all modern browsers

---

## Version 1.0.0 - Initial Release

### Features
- User authentication (JWT-based)
- Product search functionality
- Multi-platform scraping (Amazon)
- Real-time search status updates
- Interactive dashboard
- Search history
- Profile management
- Modern, responsive UI with Tailwind CSS
- Glass-morphism effects
- Animated components
- Interactive hover states

---

## Upcoming Features

### v2.1.0 (Planned)
- [ ] Google OAuth integration
- [ ] Real-time WebSocket updates
- [ ] CSV data parsing and visualization
- [ ] Export functionality (PDF, Excel)
- [ ] Email notifications

### v2.2.0 (Planned)
- [ ] Custom theme colors
- [ ] High contrast mode
- [ ] Time-based auto theme switching
- [ ] Scheduled searches
- [ ] Search templates

### v3.0.0 (Future)
- [ ] Mobile app
- [ ] Advanced analytics
- [ ] Team collaboration
- [ ] API integrations
- [ ] Custom dashboards

---

## Migration Guide

### Updating from v1.0.0 to v2.0.0

1. **Update dependencies:**
   ```bash
   npm install
   ```

2. **Clear browser cache:**
   - Press Ctrl+Shift+R (Windows/Linux)
   - Press Cmd+Shift+R (Mac)

3. **Update environment variables:**
   ```bash
   # .env
   VITE_APP_NAME=Insight Stream  # Changed from "E-Commerce Scraper"
   ```

4. **Theme preference:**
   - Theme automatically detects system preference
   - Users can manually toggle using navbar button
   - Preference saved in localStorage

5. **Logout fix:**
   - Logout now properly clears all cached data
   - No need to manually clear localStorage

---

## Breaking Changes

### v2.0.0
- Platform name changed (update any external references)
- Theme context required (ensure ThemeProvider wraps app)
- None for existing functionality - all backward compatible

---

## Known Issues

### v2.0.0
- None reported

### v1.0.0
- ✅ FIXED: Logout didn't clear React Query cache
- ✅ FIXED: User data persisted between different accounts

---

## Contributors

- Development Team
- UI/UX Design Team
- Testing Team

---

**For detailed dark mode documentation, see [DARK_MODE_GUIDE.md](./DARK_MODE_GUIDE.md)**
