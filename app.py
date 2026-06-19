"""
Streamlit App for Cardamom Price History Dashboard
Displays interactive charts with data filters and controls
Reads data from SQLite database
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Cardamom Price Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def load_database():
    """Load data from SQLite database"""
    db_name = 'cardamom_data.db'
    
    if not os.path.exists(db_name):
        return None
    
    try:
        conn = sqlite3.connect(db_name)
        df = pd.read_sql_query(
            'SELECT date_of_auction, auctioneer, total_qty_arrived, max_price, avg_price FROM cardamom_prices ORDER BY date_of_auction',
            conn
        )
        conn.close()
        
        # Convert date column to datetime
        df['date_of_auction'] = pd.to_datetime(df['date_of_auction'])
        
        return df
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return None


def initialize_database_in_app():
    """Bootstrap database in Streamlit runtime when DB file is missing."""
    try:
        from scraper import main_scrape_auto
        return main_scrape_auto()
    except Exception as e:
        st.error(f"Failed to initialize data: {e}")
        return False

def create_interactive_chart(df, show_maxprice, show_avgprice, show_quantity, show_markers):
    """
    Create interactive Plotly chart with dual Y-axes
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Determine marker style
    marker_mode = 'lines+markers' if show_markers else 'lines'
    marker_size = 4 if show_markers else 0
    
    # Add MaxPrice trace (primary y-axis)
    if show_maxprice:
        fig.add_trace(
            go.Scatter(
                x=df['date_of_auction'],
                y=df['max_price'],
                name='MaxPrice (Rs./Kg)',
                mode=marker_mode,
                line=dict(color='blue', width=2),
                marker=dict(size=marker_size),
                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>MaxPrice:</b> %{y:.2f} Rs./Kg<extra></extra>',
            ),
            secondary_y=False,
        )
    
    # Add AvgPrice trace (primary y-axis)
    if show_avgprice:
        fig.add_trace(
            go.Scatter(
                x=df['date_of_auction'],
                y=df['avg_price'],
                name='Avg.Price (Rs./Kg)',
                mode=marker_mode,
                line=dict(color='cyan', width=2),
                marker=dict(size=marker_size),
                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Avg Price:</b> %{y:.2f} Rs./Kg<extra></extra>',
            ),
            secondary_y=False,
        )
    
    # Add Total Qty Arrived trace (secondary y-axis)
    if show_quantity:
        fig.add_trace(
            go.Scatter(
                x=df['date_of_auction'],
                y=df['total_qty_arrived'],
                name='Total Qty Arrived (Kgs)',
                mode=marker_mode,
                line=dict(color='orange', width=2),
                marker=dict(size=marker_size),
                hovertemplate='<b>Date:</b> %{x|%Y-%m-%d}<br><b>Total Qty:</b> %{y:,.0f} Kgs<extra></extra>',
            ),
            secondary_y=True,
        )
    
    # Update layout
    fig.update_layout(
        title='Cardamom Price History with Quantity Arrived',
        hovermode='x unified',
        height=600,
        template='plotly_white',
        font=dict(size=12),
        xaxis_rangeslider_visible=False,
    )
    
    # Update axes
    fig.update_xaxes(title_text='Date of Auction')
    fig.update_yaxes(title_text='Price (Rs./Kg)', secondary_y=False)
    fig.update_yaxes(title_text='Total Qty Arrived (Kgs)', secondary_y=True)
    
    return fig

def display_statistics(df):
    """Display summary statistics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Records",
            f"{len(df):,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Avg Price Range",
            f"Rs. {df['avg_price'].min():.2f} - {df['avg_price'].max():.2f}",
            delta=None
        )
    
    with col3:
        st.metric(
            "Total Qty (All Time)",
            f"{df['total_qty_arrived'].sum():,.0f} Kgs",
            delta=None
        )
    
    with col4:
        latest_date = df['date_of_auction'].max()
        oldest_date = df['date_of_auction'].min()
        days_span = (latest_date - oldest_date).days
        st.metric(
            "Data Span",
            f"{days_span} days",
            delta=None
        )

def main():
    # Header
    st.title("📊 Cardamom Price Dashboard")
    st.markdown("Interactive dashboard for Indian Cardamom Daily Auction Prices")
    st.markdown("Data source: [Indian Spices Board](https://www.indianspices.com/marketing/price/domestic/daily-price-small.html)")
    
    # Load data
    df = load_database()
    
    if df is None or len(df) == 0:
        st.warning("No database/data found yet.")
        st.info("Click the button below to fetch latest data from the source website and initialize the dashboard.")

        if st.button("Initialize Data Now", type="primary"):
            with st.spinner("Fetching data and creating database..."):
                ok = initialize_database_in_app()

            if ok:
                st.success("Data initialized successfully. Reloading dashboard...")
                st.rerun()
            else:
                st.error("Could not initialize data from source website. Please try again after a minute.")
        return
    
    # Sidebar controls
    st.sidebar.title("📋 Chart Controls")
    
    # Data visibility toggles
    st.sidebar.markdown("### Series Visibility")
    show_maxprice = st.sidebar.checkbox("Show MaxPrice", value=True)
    show_avgprice = st.sidebar.checkbox("Show Avg.Price", value=True)
    show_quantity = st.sidebar.checkbox("Show Quantity Arrived", value=True)
    show_markers = st.sidebar.checkbox("Show Markers", value=False)
    
    # Date range filter
    st.sidebar.markdown("### Date Range Filter")
    
    min_date = df['date_of_auction'].min().date()
    max_date = df['date_of_auction'].max().date()
    
    # Quick presets
    preset = st.sidebar.selectbox(
        "Quick Select:",
        ["Custom", "Last 3 Months", "Last 6 Months", "Last 1 Year", "All Data"]
    )
    
    if preset == "Last 3 Months":
        start_date = (pd.Timestamp.now() - timedelta(days=90)).date()
        end_date = max_date
    elif preset == "Last 6 Months":
        start_date = (pd.Timestamp.now() - timedelta(days=180)).date()
        end_date = max_date
    elif preset == "Last 1 Year":
        start_date = (pd.Timestamp.now() - timedelta(days=365)).date()
        end_date = max_date
    elif preset == "All Data":
        start_date = min_date
        end_date = max_date
    else:  # Custom
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)
    
    # Filter data
    filtered_df = df[
        (df['date_of_auction'].dt.date >= start_date) &
        (df['date_of_auction'].dt.date <= end_date)
    ].copy()
    
    if len(filtered_df) == 0:
        st.warning("No data available for the selected date range")
        return
    
    # Display statistics
    st.markdown("---")
    st.subheader("📈 Key Metrics")
    display_statistics(filtered_df)
    
    # Display chart
    st.markdown("---")
    st.subheader("📊 Interactive Chart")
    
    fig = create_interactive_chart(filtered_df, show_maxprice, show_avgprice, show_quantity, show_markers)
    st.plotly_chart(fig, use_container_width=True)
    
    # Display data table
    st.markdown("---")
    st.subheader("📋 Data Table")
    
    with st.expander("View Detailed Data"):
        # Prepare display dataframe
        display_df = filtered_df.copy()
        display_df['Date'] = display_df['date_of_auction'].dt.strftime('%Y-%m-%d')
        display_df['Auctioneer'] = display_df['auctioneer'].str.title()
        display_df['Qty (Kgs)'] = display_df['total_qty_arrived'].apply(lambda x: f"{x:,.0f}")
        display_df['Max Price (Rs./Kg)'] = display_df['max_price'].apply(lambda x: f"{x:.2f}")
        display_df['Avg Price (Rs./Kg)'] = display_df['avg_price'].apply(lambda x: f"{x:.2f}")
        
        show_cols = ['Date', 'Auctioneer', 'Qty (Kgs)', 'Max Price (Rs./Kg)', 'Avg Price (Rs./Kg)']
        st.dataframe(display_df[show_cols], use_container_width=True, height=400)
        
        # Download button
        csv = display_df[show_cols].to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"cardamom_prices_{start_date}_{end_date}.csv",
            mime="text/csv"
        )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>💾 Data updated daily via automated web scraper</p>
        <p>Last updated: {} | Total records: {:,}</p>
        <p><small>Dashboard built with Streamlit | Data source: Indian Spices Board</small></p>
    </div>
    """.format(
        df['date_of_auction'].max().strftime('%Y-%m-%d %H:%M'),
        len(df)
    ), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
