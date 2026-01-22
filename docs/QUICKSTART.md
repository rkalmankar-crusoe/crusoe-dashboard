# Quick Start Guide

## Get the Dashboard Running in 60 Seconds

### Option 1: Open Directly (Fastest)

1. Navigate to the frontend directory:
   ```bash
   cd crusoe-dashboard/frontend
   ```

2. Open `index.html` in your browser:
   - **macOS**: `open index.html`
   - **Linux**: `xdg-open index.html`
   - **Windows**: Double-click `index.html`

That's it! The dashboard will load with default data.

### Option 2: Local Web Server (Recommended)

If you want to fetch data from JSON files dynamically:

1. Start a simple HTTP server:
   ```bash
   cd crusoe-dashboard/frontend
   python3 -m http.server 8000
   ```

2. Open browser to: `http://localhost:8000`

### Option 3: Full Setup with Live Data

1. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

2. Set your API key:
   ```bash
   export CRUSOE_API_KEY="your-api-key-here"
   ```

3. Update metrics:
   ```bash
   python backend/scripts/update_metrics.py
   ```

4. Open the dashboard (see Option 1 or 2)

## Next Steps

- **Customize**: Edit `backend/data/metrics.json` with your own data
- **Automate**: Set up cron job for periodic updates
- **Integrate**: Connect to Crusoe Cloud API for live data
- **Deploy**: Host on GitHub Pages, Netlify, or your web server

## Troubleshooting

**Dashboard doesn't load?**
- Make sure you're opening `index.html` from the `frontend/` directory
- Check browser console for errors (F12)

**Data not updating?**
- Verify `metrics.json` exists in `backend/data/`
- Check Python script output for errors
- Ensure API credentials are set correctly

**Styles look broken?**
- Verify `css/styles.css` exists
- Check file paths in `index.html`
- Clear browser cache (Ctrl+Shift+R / Cmd+Shift+R)

## File Locations

```
crusoe-dashboard/
├── frontend/
│   ├── index.html          ← Open this file
│   ├── css/styles.css      ← Dashboard styles
│   └── js/dashboard.js     ← Interactive features
└── backend/
    ├── data/metrics.json   ← Data source
    └── scripts/update_metrics.py  ← Data updater
```
