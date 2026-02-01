"""
Weekly Sales Aggregation and Visualization for eBay Sold Listings.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np


def load_listings(filepath):
    """Load listings from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def aggregate_by_week(listings, recent_days=90):
    """Group listings by ISO week and count items sold.

    Args:
        listings: List of listing dicts with sold_date
        recent_days: Only include listings from the last N days (default 90).
                     eBay only provides reliable data for ~90 days.
    """
    df = pd.DataFrame(listings)

    # Filter out listings without sold dates
    df = df[df['sold_date'].notna()].copy()

    if df.empty:
        print("No listings with valid sold dates found.")
        return pd.DataFrame()

    # Convert to datetime
    df['sold_date'] = pd.to_datetime(df['sold_date'])

    # Filter to recent data only (eBay's reliable window)
    if recent_days:
        cutoff = datetime.now() - timedelta(days=recent_days)
        original_count = len(df)
        df = df[df['sold_date'] >= cutoff].copy()
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            print(f"Note: Filtered out {filtered_count} listings older than {recent_days} days (eBay data limitation)")

    # Create year-week identifier using ISO calendar
    df['year'] = df['sold_date'].dt.isocalendar().year
    df['week'] = df['sold_date'].dt.isocalendar().week
    df['year_week'] = df['year'].astype(str) + '-W' + df['week'].astype(str).str.zfill(2)

    # Get the Monday of each week for plotting
    df['week_start'] = df['sold_date'].apply(
        lambda x: x - timedelta(days=x.weekday())
    )

    # Aggregate by week
    weekly = df.groupby(['year_week', 'week_start']).agg(
        items_sold=('title', 'count'),
        avg_price=('price', 'mean'),
        total_revenue=('price', 'sum'),
        min_price=('price', 'min'),
        max_price=('price', 'max')
    ).reset_index()

    # Sort by date
    weekly = weekly.sort_values('week_start').reset_index(drop=True)

    return weekly


def fill_missing_weeks(weekly_data):
    """Fill in any missing weeks with zero values."""
    if weekly_data.empty:
        return weekly_data

    # Get date range
    min_date = weekly_data['week_start'].min()
    max_date = weekly_data['week_start'].max()

    # Create all weeks in range
    all_weeks = pd.date_range(start=min_date, end=max_date, freq='W-MON')
    all_weeks_df = pd.DataFrame({'week_start': all_weeks})

    # Merge with actual data
    complete = all_weeks_df.merge(weekly_data, on='week_start', how='left')

    # Fill missing values
    complete['items_sold'] = complete['items_sold'].fillna(0).astype(int)
    complete['year_week'] = complete['week_start'].apply(
        lambda x: f"{x.isocalendar().year}-W{x.isocalendar().week:02d}"
    )

    return complete


def plot_weekly_sales(weekly_data, output_path='data/weekly_sales.png'):
    """Create time series bar chart of weekly sales."""
    if weekly_data.empty:
        print("No data to plot.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))

    # Bar chart
    bars = ax.bar(
        weekly_data['week_start'],
        weekly_data['items_sold'],
        width=5,
        alpha=0.7,
        color='steelblue',
        edgecolor='navy',
        label='Items Sold'
    )

    # Add trend line
    x_numeric = np.arange(len(weekly_data))
    if len(weekly_data) > 1:
        z = np.polyfit(x_numeric, weekly_data['items_sold'], 1)
        p = np.poly1d(z)
        ax.plot(
            weekly_data['week_start'],
            p(x_numeric),
            'r--',
            linewidth=2,
            label=f'Trend (slope: {z[0]:.2f}/week)'
        )

    # Formatting
    ax.set_xlabel('Week', fontsize=12)
    ax.set_ylabel('Number of Items Sold', fontsize=12)
    ax.set_title('No Rarity 1996 Pokemon Cards - Weekly eBay Sales', fontsize=14, fontweight='bold')

    # Format x-axis dates
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    plt.xticks(rotation=45, ha='right')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.annotate(
                f'{int(height)}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center',
                va='bottom',
                fontsize=8
            )

    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)

    # Add summary stats
    total_sold = weekly_data['items_sold'].sum()
    avg_per_week = weekly_data['items_sold'].mean()
    stats_text = f'Total: {int(total_sold)} items | Avg: {avg_per_week:.1f}/week'
    ax.text(
        0.02, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    )

    plt.tight_layout()

    # Save figure
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {output_path}")

    plt.show()


def save_weekly_csv(weekly_data, output_path='data/weekly_sales.csv'):
    """Save weekly data to CSV."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Select and rename columns for export
    export_df = weekly_data[['year_week', 'week_start', 'items_sold']].copy()
    export_df['week_start'] = export_df['week_start'].dt.strftime('%Y-%m-%d')

    export_df.to_csv(output, index=False)
    print(f"Data saved to {output_path}")


def print_summary(weekly_data, listings):
    """Print summary statistics."""
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    if weekly_data.empty:
        print("No data available.")
        return

    total_items = weekly_data['items_sold'].sum()
    num_weeks = len(weekly_data)
    avg_per_week = weekly_data['items_sold'].mean()
    max_week = weekly_data.loc[weekly_data['items_sold'].idxmax()]
    min_week = weekly_data.loc[weekly_data['items_sold'].idxmin()]

    print(f"Date range: {weekly_data['week_start'].min().strftime('%Y-%m-%d')} to "
          f"{weekly_data['week_start'].max().strftime('%Y-%m-%d')}")
    print(f"Total weeks analyzed: {num_weeks}")
    print(f"Total items sold: {int(total_items)}")
    print(f"Average per week: {avg_per_week:.1f}")
    print(f"Best week: {max_week['year_week']} ({int(max_week['items_sold'])} items)")
    print(f"Slowest week: {min_week['year_week']} ({int(min_week['items_sold'])} items)")

    # Price stats if available
    valid_prices = [l['price'] for l in listings if l.get('price')]
    if valid_prices:
        print(f"\nPrice range: ${min(valid_prices):.2f} - ${max(valid_prices):.2f}")
        print(f"Average price: ${sum(valid_prices)/len(valid_prices):.2f}")

    print("=" * 50)


if __name__ == '__main__':
    # Test with sample data
    sample_listings = [
        {'title': 'Test Card 1', 'price': 50.0, 'sold_date': '2026-01-10'},
        {'title': 'Test Card 2', 'price': 75.0, 'sold_date': '2026-01-11'},
        {'title': 'Test Card 3', 'price': 100.0, 'sold_date': '2026-01-05'},
    ]

    weekly = aggregate_by_week(sample_listings)
    print(weekly)
