# Deployment Guide

## GitHub Pages Deployment

### Prerequisites
1. GitHub repository must be **public** (or GitHub Pro for private repos)
2. Files needed for GitHub Pages:
   - `index.html` ✅
   - `static-predictor.js` ✅
   - `sop_data.json` ✅

### Steps to Deploy

1. **Check if repo is public:**
   ```bash
   cd /Users/yarkin.akcil/Documents/GitHub/SOPSlack
   git remote -v
   ```

2. **Make repo public (if needed):**
   - Go to GitHub repository settings
   - Scroll to "Danger Zone"
   - Click "Change visibility" → "Make public"

3. **Push files to GitHub:**
   ```bash
   git add index.html static-predictor.js sop_data.json
   git commit -m "Add GitHub Pages support"
   git push origin main
   ```

4. **Enable GitHub Pages:**
   - Go to repository Settings
   - Click "Pages" in left sidebar
   - Under "Source", select "Deploy from a branch"
   - Select branch: `main`
   - Select folder: `/ (root)`
   - Click "Save"

5. **Access your site:**
   - URL will be: `https://yarkin.akcil.github.io/SOPSlack/`
   - Or check in Settings → Pages for the exact URL

### Optional: Add Gemini Pro API (for ML predictions)

If you want AI-powered predictions, you'll need to run the backend:

1. **Add Gemini API key to `.env`:**
   ```bash
   echo "GEMINI_API_KEY=your_key_here" >> .env
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run backend:**
   ```bash
   python app.py
   ```

4. **Update frontend to use backend:**
   - Change `predictor.js` instead of `static-predictor.js` in `index.html`
   - Set API_URL to your backend URL

## Local Testing

To test locally before deploying:

```bash
# Simple HTTP server
python3 -m http.server 8000

# Or use Node.js
npx http-server -p 8000
```

Then open: http://localhost:8000

## Files Overview

### Frontend (GitHub Pages compatible)
- `index.html` - Main web interface
- `static-predictor.js` - Client-side prediction (no backend needed)
- `sop_data.json` - SOP content database

### Backend (Optional - for AI predictions)
- `app.py` - Flask API server
- `final_predictor.py` - Prediction logic
- `complete_sop_mapping.py` - SOP mapping
- `requirements.txt` - Python dependencies

### Configuration
- `.env` - API keys (DO NOT COMMIT!)
- `.gitignore` - Files to ignore

## Troubleshooting

### Issue: 404 on GitHub Pages
- Make sure repository is public
- Check that `index.html` is in root directory
- Wait a few minutes after enabling Pages

### Issue: SOP data not loading
- Check browser console for errors
- Verify `sop_data.json` exists and is valid JSON
- Check file permissions

### Issue: Predictions not working
- The static version uses rule-based predictions only
- For ML predictions, you need to run the backend server
- Make sure `.env` has the correct API keys

## Need Help?

Contact: yarkin.akcil@gusto.com

