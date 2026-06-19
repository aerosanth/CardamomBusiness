# 🌿 Cardamom Business - Price History Dashboard

An automated web scraping and data visualization solution for Indian Cardamom Daily Auction Prices.

**Live Dashboard:** [Streamlit Cloud](https://cardamom-business.streamlit.app) *(Coming Soon)*

---

## 📊 Features

- ✅ **Interactive Dashboard** - Real-time price charts with hover tooltips
- ✅ **Dual Y-Axes** - Price (Rs./Kg) and Quantity (Kgs) on separate scales
- ✅ **Toggle Controls** - Show/Hide MaxPrice, Avg.Price, and Quantity lines
- ✅ **Marker Toggle** - Display data points on chart
- ✅ **Date Range Filter** - Quick presets (3m, 6m, 1y, All) or custom range
- ✅ **Zoom & Pan** - Plotly's interactive chart controls
- ✅ **Data Export** - Download filtered data as CSV
- ✅ **Automated Scraping** - Daily data collection via GitHub Actions
- ✅ **Incremental Updates** - Only fetches new dates (efficient)
- ✅ **Cloud Storage** - SQLite database in GitHub repo

---

## 🏗️ Project Structure

```
CardamomBusiness/
├── app.py                          # Streamlit application
├── scraper.py                      # Web scraper script
├── requirements.txt                # Python dependencies
├── cardamom_data.db               # SQLite database (auto-generated)
├── .github/
│   └── workflows/
│       └── daily_scrape.yml       # GitHub Actions workflow
└── README.md                       # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- GitHub account

### 1. Clone the Repository

```bash
git clone https://github.com/ansSanthoshM/CardamomBusiness.git
cd CardamomBusiness
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Initial Data Collection (One-time)

```bash
python scraper.py
```

This scrapes all historical data from the website and creates `cardamom_data.db`.

**Note:** First scrape may take 5-10 minutes depending on website response time.

### 5. Run Streamlit App Locally

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

---

## 📈 How It Works

### Initial Setup

1. **Full Historical Scrape** - Downloads all available data from the website
2. **Data Cleaning** - Converts formats, removes duplicates
3. **SQLite Storage** - Saves to `cardamom_data.db` for fast access

### Daily Updates (Automated)

1. **GitHub Actions Trigger** - Runs every day at 6:00 AM UTC
2. **Incremental Scrape** - Fetches only recent pages (~last 3 pages)
3. **New Records Only** - Inserts only dates not in database (via UNIQUE constraint)
4. **Auto-Commit** - Pushes updated database to GitHub
5. **Streamlit Refresh** - Cloud app detects changes and refreshes automatically

### Data Flow

```
Website (indianspices.com)
    ↓
scraper.py (BeautifulSoup)
    ↓
Clean & Validate
    ↓
SQLite Database (cardamom_data.db)
    ↓
Streamlit App (app.py)
    ↓
Interactive Dashboard
```

---

## 🌐 Deploy to Streamlit Cloud

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Initial commit: Cardamom dashboard"
git push origin main
```

### Step 2: Create Streamlit Cloud Account

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"

### Step 3: Deploy

- Repository: `ansSanthoshM/CardamomBusiness`
- Branch: `main`
- Main file path: `app.py`

Click "Deploy" and wait 2-3 minutes.

### Step 4: Embed in Google Sites

1. Copy your Streamlit app URL
2. In Google Sites: **Add → Embed code**
3. Paste:
   ```html
   <iframe src="YOUR_STREAMLIT_URL" width="100%" height="1200"></iframe>
   ```

---

## 📅 GitHub Actions Configuration

Daily scraping is automated via `.github/workflows/daily_scrape.yml`

**Schedule:** Every day at 6:00 AM UTC (11:30 AM IST)

**To modify schedule:**
1. Edit `.github/workflows/daily_scrape.yml`
2. Change the cron schedule (line 6)

Cron format: `minute hour day month weekday`

Examples:
- `0 6 * * *` = Daily at 6:00 AM UTC
- `0 */6 * * *` = Every 6 hours
- `0 10 * * 1-5` = Weekdays at 10:00 AM UTC

---

## 🔧 Configuration

### Modify Scraping Frequency

Edit `scraper.py`, function `main_scrape_incremental()`:

```python
raw_data = scrape_all_pages(max_pages=3)  # Change max_pages here
```

### Modify GitHub Actions Schedule

Edit `.github/workflows/daily_scrape.yml`:

```yaml
- cron: '0 6 * * *'  # Change this cron expression
```

### Add Database Backup

Add to `.github/workflows/daily_scrape.yml`:

```yaml
- name: Create backup
  run: cp cardamom_data.db cardamom_data.backup.db
```

---

## 📊 Dashboard Features in Detail

### Chart Controls (Sidebar)

- **Series Visibility**: Toggle MaxPrice, Avg.Price, Quantity
- **Show Markers**: Add/remove data point markers on lines
- **Date Range**: Quick presets or custom range selection

### Interactive Chart

- **Hover**: View exact date and values
- **Zoom**: Click and drag to zoom into date range
- **Pan**: Shift + drag to move around
- **Double-click**: Reset to full view
- **Legend Click**: Hide/show individual lines

### Data Table

- View detailed data for selected date range
- Download as CSV

### Key Metrics

- Total Records
- Average Price Range
- Total Quantity (all time)
- Data Span (days)

---

## 🐛 Troubleshooting

### Database not found

```
Error: Database 'cardamom_data.db' not found
```

**Solution:** Run initial scraper first
```bash
python scraper.py
```

### Website scraping fails

**Common causes:**
- Website structure changed
- Rate limiting (too many requests)
- Network issues

**Solutions:**
1. Check website manually for format changes
2. Edit `scraper.py` if HTML structure changed
3. Increase delay: `time.sleep(3)` instead of 2

### GitHub Actions not running

1. Check `.github/workflows/daily_scrape.yml` syntax
2. Go to GitHub repo → Actions → Check workflow status
3. Enable Actions in repo settings

### Streamlit app is slow

**Optimize:**
1. Reduce date range in filters
2. Disable markers if not needed
3. Clear Streamlit cache: Press 'C' in app

---

## 📝 Data Schema

**cardamom_prices table:**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| date_of_auction | TEXT | Auction date (YYYY-MM-DD) |
| auctioneer | TEXT | Auction location/name |
| no_of_lots | REAL | Number of lots auctioned |
| total_qty_arrived | REAL | Total quantity in Kgs |
| qty_sold | REAL | Quantity sold in Kgs |
| max_price | REAL | Max price in Rs./Kg |
| avg_price | REAL | Average price in Rs./Kg |
| scraped_date | TIMESTAMP | When record was scraped |

---

## 📚 Technical Stack

| Component | Technology |
|-----------|-----------|
| **Web Scraping** | BeautifulSoup4, Requests |
| **Data Processing** | Pandas, NumPy |
| **Database** | SQLite3 |
| **Dashboard** | Streamlit, Plotly |
| **Automation** | GitHub Actions |
| **Version Control** | Git, GitHub |
| **Hosting** | Streamlit Cloud |

---

## 📄 License

This project is open source and available for personal and educational use.

---

## 👤 Author

**Santhosh M**
- GitHub: [@ansSanthoshM](https://github.com/ansSanthoshM)
- Website: [Santh2 Products](https://sites.google.com/view/santh2products)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## ⚠️ Disclaimer

This project is for educational purposes. Ensure you comply with the website's terms of service and robots.txt before scraping. Add appropriate delays between requests to avoid overloading the server.

---

## 📞 Support

For issues, questions, or suggestions, please create a GitHub issue or contact the author.

---

**Last Updated:** 2026-06-19
**Status:** Active Development ✓
