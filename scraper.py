"""
Web Scraper for Indian Spices Cardamom Daily Price Data
Scrapes from: https://www.indianspices.com/marketing/price/domestic/daily-price-small.html
Stores data in SQLite database with incremental updates
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import sqlite3
from datetime import datetime
import time
import os
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Database configuration
DB_NAME = 'cardamom_data.db'
# Control how many pages to scrape from source.
# Set to an integer (e.g., 5) for limited pages or 'all' for full history.
No_Pages_to_collect_data_from_source = 5


def log(message, level="INFO"):
    """Timestamped logger with flush so messages appear in hosted logs immediately."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {message}", flush=True)

def create_database():
    """Create SQLite database with proper schema if it doesn't exist"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cardamom_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_of_auction TEXT UNIQUE NOT NULL,
            auctioneer TEXT,
            no_of_lots REAL,
            total_qty_arrived REAL,
            qty_sold REAL,
            max_price REAL,
            avg_price REAL,
            scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    log(f"Database '{DB_NAME}' initialized")

def get_last_scraped_date():
    """Get the last date that was scraped"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(date_of_auction) FROM cardamom_prices')
        result = cursor.fetchone()[0]
        conn.close()
        return result
    except:
        return None


def has_existing_data():
    """Return True when database exists and contains at least one row."""
    if not os.path.exists(DB_NAME):
        return False

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM cardamom_prices')
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False

def scrape_page(page_num=1):
    """
    Scrape a single page from the website
    
    Args:
        page_num: Page number to scrape (default: 1)
    
    Returns:
        DataFrame with scraped data
    """
    url = f'https://www.indianspices.com/marketing/price/domestic/daily-price-small.html?page={page_num}'
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        log(f"Scraping page {page_num}...")
        response = requests.get(url, headers=headers, timeout=20, verify=False)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        expected_cols = [
            'Date of Auction', 'Auctioneer', 'No.of Lots',
            'Total Qty Arrived (Kgs)', 'Qty Sold (Kgs)',
            'MaxPrice (Rs./Kg)', 'Avg.Price (Rs./Kg)'
        ]

        df = None
        # Find the actual auction table (page has multiple tables).
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows:
                continue

            header = None
            data_rows = []
            for tr in rows:
                cells = [c.get_text(' ', strip=True) for c in tr.find_all(['th', 'td'])]
                if not cells:
                    continue

                if 'Date of Auction' in cells and 'Auctioneer' in cells:
                    header = cells
                    continue

                if header and len(cells) >= len(header):
                    data_rows.append(cells[:len(header)])

            if header and data_rows:
                candidate = pd.DataFrame(data_rows, columns=header)
                if 'Date of Auction' in candidate.columns and 'Auctioneer' in candidate.columns:
                    df = candidate
                    break

        if df is None:
            log(f"No auction data table found on page {page_num}", "WARN")
            return None

        if 'Sno' in df.columns:
            df = df.drop(columns=['Sno'])

        # Remove accidental repeated header rows if present inside table body.
        if 'Date of Auction' in df.columns:
            df = df[df['Date of Auction'] != 'Date of Auction']

        available_cols = [c for c in expected_cols if c in df.columns]
        if available_cols:
            df = df[available_cols]

        if len(df) > 0:
            log(f"Scraped {len(df)} records from page {page_num}")
            return df

        log(f"No data rows found on page {page_num}", "WARN")
        return None

    except (requests.exceptions.RequestException, ValueError) as e:
        log(f"Error scraping page {page_num}: {e}", "ERROR")
        return None

def scrape_all_pages(max_pages=None):
    """
    Scrape all pages from the website
    
    Args:
        max_pages: Maximum pages to scrape (None = all available)
    
    Returns:
        Combined DataFrame from all pages
    """
    all_data = []
    page = 1
    
    while True:
        if max_pages and page > max_pages:
            break
        
        df = scrape_page(page)
        
        if df is None or len(df) == 0:
            log(f"Reached end of pages at page {page}")
            break
        
        all_data.append(df)
        running_total = sum(len(x) for x in all_data)
        log(f"Progress: page {page} collected, running rows={running_total}")
        
        # Be respectful to the website
        time.sleep(2)
        page += 1
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        return combined_df
    else:
        return None

def clean_data(df):
    """
    Clean and normalize the scraped data
    
    Args:
        df: Raw DataFrame from scraper
    
    Returns:
        Cleaned DataFrame
    """
    # Rename columns to match our database schema
    column_mapping = {
        'Date of Auction': 'date_of_auction',
        'Auctioneer': 'auctioneer',
        'No.of Lots': 'no_of_lots',
        'Total Qty Arrived (Kgs)': 'total_qty_arrived',
        'Qty Sold (Kgs)': 'qty_sold',
        'MaxPrice (Rs./Kg)': 'max_price',
        'Avg.Price (Rs./Kg)': 'avg_price'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Convert to numeric types
    numeric_cols = ['no_of_lots', 'total_qty_arrived', 'qty_sold', 'max_price', 'avg_price']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Convert date
    if 'date_of_auction' in df.columns:
        df['date_of_auction'] = pd.to_datetime(df['date_of_auction']).dt.strftime('%Y-%m-%d')
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['date_of_auction'])
    
    return df

def save_to_database(df):
    """
    Save DataFrame to SQLite database (incremental update)
    
    Args:
        df: Cleaned DataFrame to save
    
    Returns:
        Number of new records inserted
    """
    conn = sqlite3.connect(DB_NAME)
    
    # Count existing records
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM cardamom_prices')
    existing_count = cursor.fetchone()[0]
    
    # Insert new records (will skip duplicates due to UNIQUE constraint)
    try:
        for idx, row in df.iterrows():
            cursor.execute('''
                INSERT OR IGNORE INTO cardamom_prices 
                (date_of_auction, auctioneer, no_of_lots, total_qty_arrived, qty_sold, max_price, avg_price)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', tuple(row))
        
        conn.commit()
        
        # Count new records
        cursor.execute('SELECT COUNT(*) FROM cardamom_prices')
        new_count = cursor.fetchone()[0]
        inserted = new_count - existing_count
        
        log(f"Inserted {inserted} new records to database")
        log(f"Total records in database: {new_count}")
        
        return inserted
        
    except Exception as e:
        log(f"Error saving to database: {e}", "ERROR")
        conn.rollback()
        return 0
    finally:
        conn.close()

def load_from_database():
    """
    Load all data from SQLite database
    
    Returns:
        DataFrame with all cardamom price data
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        df = pd.read_sql_query('SELECT * FROM cardamom_prices', conn)
        conn.close()
        
        # Convert date column to datetime
        df['date_of_auction'] = pd.to_datetime(df['date_of_auction'])
        df = df.sort_values('date_of_auction')
        
        return df
    except Exception as e:
        log(f"Error loading from database: {e}", "ERROR")
        return None

def main_scrape_initial():
    """
    Initial full scrape - gets all historical data
    Run this once to populate the database
    """
    log("=" * 80)
    log("CARDAMOM PRICE SCRAPER - INITIAL FULL SCRAPE")
    log("=" * 80)
    
    create_database()
    
    # Scrape pages based on configuration.
    max_pages = None if str(No_Pages_to_collect_data_from_source).lower() == 'all' else int(No_Pages_to_collect_data_from_source)
    log(f"Scraping pages from website with setting: {No_Pages_to_collect_data_from_source}")
    raw_data = scrape_all_pages(max_pages=max_pages)
    
    if raw_data is None or len(raw_data) == 0:
        log("No data scraped", "ERROR")
        return False
    
    log(f"Total records scraped: {len(raw_data)}")
    
    # Clean data
    log("Cleaning data...")
    cleaned_data = clean_data(raw_data)
    log(f"Cleaned data: {len(cleaned_data)} records")
    
    # Save to database
    log("Saving to database...")
    save_to_database(cleaned_data)
    
    log("=" * 80)
    log("INITIAL SCRAPE COMPLETE")
    log("=" * 80)
    
    return True

def main_scrape_incremental():
    """
    Incremental scrape - only gets new dates since last scrape
    Run this daily via GitHub Actions
    """
    log("=" * 80)
    log("CARDAMOM PRICE SCRAPER - INCREMENTAL UPDATE")
    log("=" * 80)
    
    create_database()
    
    last_date = get_last_scraped_date()
    log(f"Last scraped date: {last_date}")
    
    # Scrape pages based on configuration.
    max_pages = None if str(No_Pages_to_collect_data_from_source).lower() == 'all' else int(No_Pages_to_collect_data_from_source)
    log(f"Scraping pages from website with setting: {No_Pages_to_collect_data_from_source}")
    raw_data = scrape_all_pages(max_pages=max_pages)
    
    if raw_data is None or len(raw_data) == 0:
        log("No new data scraped", "ERROR")
        return False
    
    log(f"Total records scraped: {len(raw_data)}")
    
    # Clean data
    log("Cleaning data...")
    cleaned_data = clean_data(raw_data)
    log(f"Cleaned data: {len(cleaned_data)} records")
    
    # Save to database (only new records will be inserted)
    log("Updating database with new records...")
    inserted = save_to_database(cleaned_data)
    
    log("=" * 80)
    if inserted > 0:
        log(f"INCREMENTAL UPDATE COMPLETE - {inserted} NEW RECORDS ADDED")
    else:
        log("INCREMENTAL UPDATE COMPLETE - NO NEW RECORDS")
    log("=" * 80)
    
    return True


def main_scrape_auto():
    """Auto mode: full historical scrape on first run, incremental afterward."""
    if has_existing_data():
        log("Auto mode selected: existing DB found -> running incremental update")
        return main_scrape_incremental()

    log("Auto mode selected: DB absent/empty -> running initial full historical scrape")
    return main_scrape_initial()

if __name__ == "__main__":
    # Auto mode for CI/CD and manual runs.
    main_scrape_auto()
