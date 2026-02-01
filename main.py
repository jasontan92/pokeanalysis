#!/usr/bin/env python3
"""
eBay Pokemon Card Sales Analyzer

Scrapes eBay sold listings for "no rarity 1996" Pokemon cards,
aggregates by week, and generates a time series visualization.

Usage:
    python main.py
"""

from scraper import EbayScraper
from analyzer import (
    load_listings,
    aggregate_by_week,
    fill_missing_weeks,
    plot_weekly_sales,
    save_weekly_csv,
    print_summary
)


def main():
    # Configuration
    search_term = "no rarity 1996"
    max_pages = 30  # eBay typically shows ~60 items per page
    raw_data_path = "data/raw_listings.json"
    csv_output_path = "data/weekly_sales.csv"
    chart_output_path = "data/weekly_sales.png"

    print("=" * 60)
    print("eBay 'No Rarity 1996' Pokemon Card Sales Analyzer")
    print("=" * 60)

    # Step 1: Scrape eBay sold listings
    print("\n[1/4] Scraping eBay sold listings...")
    scraper = EbayScraper()
    listings = scraper.scrape_all_pages(search_term, max_pages=max_pages)

    if not listings:
        print("ERROR: No listings found. eBay may be blocking requests.")
        print("Try again later or reduce request frequency.")
        return

    print(f"\nFound {len(listings)} total sold listings")

    # Save raw data
    scraper.save_to_json(listings, raw_data_path)

    # Step 2: Aggregate by week
    print("\n[2/4] Aggregating data by week...")
    weekly_data = aggregate_by_week(listings)

    if weekly_data.empty:
        print("ERROR: No valid data to aggregate.")
        return

    # Fill missing weeks
    weekly_data = fill_missing_weeks(weekly_data)
    print(f"Data spans {len(weekly_data)} weeks")

    # Step 3: Save CSV
    print("\n[3/4] Saving weekly data to CSV...")
    save_weekly_csv(weekly_data, csv_output_path)

    # Step 4: Generate visualization
    print("\n[4/4] Generating time series plot...")
    plot_weekly_sales(weekly_data, chart_output_path)

    # Print summary
    print_summary(weekly_data, listings)

    print("\nDone! Output files:")
    print(f"  - Raw data: {raw_data_path}")
    print(f"  - Weekly CSV: {csv_output_path}")
    print(f"  - Chart: {chart_output_path}")


if __name__ == "__main__":
    main()
