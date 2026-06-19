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

# Database configuration
DB_NAME = 'cardamom_data.db'

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
    print(f"✓ Database '{DB_NAME}' initialized")

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
        print(f"Scraping page {page_num}...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table
        table = soup.find('table', {'class': 'table'})
        
        if not table:
            print(f"No table found on page {page_num}")
            return None
        
        # Extract headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.get_text(strip=True))
        
        # Extract rows
        rows = []
        for tr in table.find_all('tr')[1:]:  # Skip header row
            cols = tr.find_all('td')
            if cols:
                row = [col.get_text(strip=True) for col in cols]
                rows.append(row)
        
        if rows:
            df = pd.DataFrame(rows, columns=headers)
            print(f"✓ Scraped {len(rows)} records from page {page_num}")
            return df
        else:
            print(f"No data rows found on page {page_num}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Error scraping page {page_num}: {e}")
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
            print(f"Reached end of pages at page {page}")
            break
        
        all_data.append(df)
        
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
        
        print(f"✓ Inserted {inserted} new records to database")
        print(f"  Total records in database: {new_count}")
        
        return inserted
        
    except Exception as e:
        print(f"✗ Error saving to database: {e}")
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
        print(f"✗ Error loading from database: {e}")
        return None

def main_scrape_initial():
    """
    Initial full scrape - gets all historical data
    Run this once to populate the database
    """
    print("=" * 80)
    print("CARDAMOM PRICE SCRAPER - INITIAL FULL SCRAPE")
    print("=" * 80)
    
    create_database()
    
    # Scrape all pages
    print("\nScraping all pages from website...")
    raw_data = scrape_all_pages(max_pages=None)
    
    if raw_data is None or len(raw_data) == 0:
        print("✗ No data scraped")
        return False
    
    print(f"\n✓ Total records scraped: {len(raw_data)}")
    
    # Clean data
    print("\nCleaning data...")
    cleaned_data = clean_data(raw_data)
    print(f"✓ Cleaned data: {len(cleaned_data)} records")
    
    # Save to database
    print("\nSaving to database...")
    inserted = save_to_database(cleaned_data)
    
    print("\n" + "=" * 80)
    print("INITIAL SCRAPE COMPLETE")
    print("=" * 80)
    
    return True

def main_scrape_incremental():
    """
    Incremental scrape - only gets new dates since last scrape
    Run this daily via GitHub Actions
    """
    print("=" * 80)
    print("CARDAMOM PRICE SCRAPER - INCREMENTAL UPDATE")
    print("=" * 80)
    
    create_database()
    
    last_date = get_last_scraped_date()
    print(f"\nLast scraped date: {last_date}")
    
    # Scrape first 3 pages (usually contains recent data)
    print("\nScraping recent pages from website...")
    raw_data = scrape_all_pages(max_pages=3)
    
    if raw_data is None or len(raw_data) == 0:
        print("✗ No new data scraped")
        return False
    
    print(f"\n✓ Total records scraped: {len(raw_data)}")
    
    # Clean data
    print("\nCleaning data...")
    cleaned_data = clean_data(raw_data)
    print(f"✓ Cleaned data: {len(cleaned_data)} records")
    
    # Save to database (only new records will be inserted)
    print("\nUpdating database with new records...")
    inserted = save_to_database(cleaned_data)
    
    print("\n" + "=" * 80)
    if inserted > 0:
        print(f"INCREMENTAL UPDATE COMPLETE - {inserted} NEW RECORDS ADDED")
    else:
        print("INCREMENTAL UPDATE COMPLETE - NO NEW RECORDS")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    # For testing: run incremental scrape
    main_scrape_incremental()
