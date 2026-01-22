# Crusoe Cloud GPU Infrastructure Dashboard

A real-time interactive dashboard for visualizing Crusoe Cloud's global GPU infrastructure across multiple datacenters.

## Features

- **Real-time Metrics**: Live GPU infrastructure data across 3 global regions
- **Interactive UI**: Smooth animations, sticky navigation, comparison mode
- **Regional Drill-down**: Detailed views for Dallas, Virginia, and Iceland datacenters
- **Performance Tiers**: Visual categorization of GPU classes (Ultra-Premium, Premium, Standard, Budget)
- **Capacity Analytics**: Reserved vs available capacity tracking
- **Vendor Distribution**: NVIDIA and AMD GPU breakdown
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices

## Architecture

```
crusoe-dashboard/
├── frontend/           # Client-side dashboard
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript logic
│   ├── assets/        # Images, icons
│   └── index.html     # Main dashboard HTML
├── backend/           # Server-side data processing
│   ├── scripts/       # Python scripts for metrics collection
│   └── data/          # JSON data files
└── docs/              # Documentation
```

## Setup

### Prerequisites

- Modern web browser (Chrome, Firefox, Safari, Edge)
- Python 3.8+ (for backend metrics collection)
- Crusoe Cloud API credentials (for live data updates)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crusoe-dashboard.git
   cd crusoe-dashboard
   ```

2. **Open the dashboard**
   ```bash
   cd frontend
   open index.html  # macOS
   # or
   xdg-open index.html  # Linux
   # or simply double-click index.html in Windows
   ```

### Backend Setup (Optional - for live data updates)

1. **Install Python dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

2. **Configure API credentials**
   ```bash
   export CRUSOE_API_KEY="your-api-key-here"
   ```

3. **Run the metrics updater**
   ```bash
   python backend/scripts/update_metrics.py
   ```

4. **Schedule automated updates** (optional)
   ```bash
   # Add to crontab for hourly updates
   0 * * * * /path/to/python /path/to/update_metrics.py
   ```

## Usage

### Dashboard Navigation

- **Tabs**: Click on Dallas, Virginia, Iceland, or Global Summary to view region-specific details
- **Comparison Mode**: Click "Compare Regions" to see side-by-side regional comparisons
- **Tooltips**: Hover over technical terms for explanations
- **Back to Top**: Scroll down to reveal the back-to-top button
- **Sticky Navigation**: Tabs stick to the top when scrolling

### Data Updates

The dashboard reads from `/backend/data/metrics.json`. Update this file using:

1. **Manual**: Edit `metrics.json` directly
2. **API**: Run `update_metrics.py` to fetch from Crusoe Cloud API
3. **Automated**: Set up cron job for periodic updates

### Customization

- **Colors**: Modify `/frontend/css/styles.css`
- **Data Structure**: Update `/backend/data/metrics.json`
- **Regions**: Add new regions in both HTML and data files
- **API Integration**: Customize `/backend/scripts/update_metrics.py`

## Data Structure

### metrics.json Format

```json
{
  "last_updated": "2026-01-22T00:00:00Z",
  "global_summary": {
    "total_nodes": 2732,
    "total_gpus": 19008,
    "monthly_revenue": 61500000,
    "available_nodes": 224
  },
  "regions": {
    "dallas": { ... },
    "virginia": { ... },
    "iceland": { ... }
  },
  "gpu_models": { ... },
  "vendors": { ... }
}
```

## API Integration

The backend script connects to Crusoe Cloud's API to fetch infrastructure metrics:

- Node counts and status
- GPU inventory and utilization
- Regional distribution
- Capacity allocation
- Revenue metrics

See `/backend/scripts/update_metrics.py` for API integration details.

## Development

### File Structure

- **index.html**: Main dashboard HTML structure
- **styles.css**: All styling and animations
- **dashboard.js**: Interactive functionality (tabs, comparison, scrolling)
- **update_metrics.py**: Backend data collection
- **metrics.json**: Data source for dashboard

### Adding New Features

1. Update HTML structure in `index.html`
2. Add styles in `styles.css`
3. Implement logic in `dashboard.js`
4. Update data structure in `metrics.json`
5. Modify API calls in `update_metrics.py` if needed

## Technologies Used

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Python 3.8+
- **Data Format**: JSON
- **API**: RESTful HTTP requests

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Email: support@example.com
- Documentation: [/docs](./docs/)

## Roadmap

- [ ] Real-time WebSocket updates
- [ ] Historical data trends and charts
- [ ] Cost optimization recommendations
- [ ] Alert system for capacity changes
- [ ] Export functionality (CSV, PDF)
- [ ] Dark/Light theme toggle
- [ ] Multi-user authentication
