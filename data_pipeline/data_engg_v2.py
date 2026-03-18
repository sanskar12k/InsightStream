# Quality check
# Cleaning
# Ranking Brand
# Ranking Products
# Pandas-based data pipeline - optimized for KB-sized datasets

import os
import sys
import pandas as pd
import numpy as np

class Config:
    APP_NAME = "EcommerceScraper"
    DATA_PATH = "./data/"
    LOG_LEVEL = "INFO"

def load_data(file_path: str, file_format: str = "csv") -> pd.DataFrame:
    """Load data from file into Pandas DataFrame"""
    if file_format == "csv":
        df = pd.read_csv(file_path)
    elif file_format == "json":
        df = pd.read_json(file_path)
    elif file_format == "parquet":
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

    return df

def save_data(df: pd.DataFrame, file_path: str, file_format: str = "csv"):
    """Save Pandas DataFrame to specified file format"""
    if file_format == "csv":
        df.to_csv(file_path, index=False)
    elif file_format == "json":
        df.to_json(file_path, orient='records', indent=2)
    elif file_format == "parquet":
        df.to_parquet(file_path, index=False)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

def check_data_quality(df: pd.DataFrame) -> bool:
    """Check if DataFrame meets basic quality checks"""
    if df is None or len(df) == 0:
        return False

    rows = len(df)

    # Check for nulls in critical columns
    critical_columns = ['name', 'cur_price']
    for col in critical_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                print(f"Critical column '{col}' has {null_count} null values")
                return False

    # If following column is empty for more than 50% of rows, fail quality check
    optional_columns = ['rating', 'review_count', 'brand']
    for col in optional_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > rows * 0.5:
                print(f"Optional column '{col}' has {null_count}/{rows} null values (>{50}%)")
                return False

    return True

def apply_data_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize DataFrame"""
    # Remove duplicates
    df = df.drop_duplicates()

    # Fill missing values
    fill_values = {
        'Rating': 0,
        'Review Count': 0,
        'Brand': 'Unknown',
        'Country of Origin': 'Unknown'
    }
    df = df.fillna(fill_values)

    # Trim whitespace from text columns
    text_columns = ["Product Name", "Brand", "Country of Origin"]
    for col_name in text_columns:
        if col_name in df.columns:
            df[col_name] = df[col_name].astype(str).str.strip()

    # Capitalize columns
    capital_columns = ["Brand", "Country of Origin"]
    for col_name in capital_columns:
        if col_name in df.columns:
            df[col_name] = df[col_name].astype(str).str.upper()

    # Ensure non-negative numeric values
    numeric_columns = ["Current Price", "Rating", "Review Count"]
    for col_name in numeric_columns:
        if col_name in df.columns:
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
            df[col_name] = df[col_name].apply(lambda x: max(0, x))

    # Rename columns for consistency
    df = df.rename(columns={
        "Review Count": "review_count",
        "Current Price": "current_price"
    })

    return df

def apply_advanced_cleaning(df: pd.DataFrame) -> pd.DataFrame:
    """Remove outliers using IQR (Interquartile Range) method"""
    if 'price_per_gram' not in df.columns:
        print("Warning: 'price_per_gram' column not found, skipping outlier removal")
        return df

    # Calculate quartiles
    q1 = df['price_per_gram'].quantile(0.25)
    q3 = df['price_per_gram'].quantile(0.75)
    iqr = q3 - q1

    # Using 1.5 * IQR for outlier detection (standard approach)
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    print(f"Price per gram outlier bounds: {lower_bound:.2f} to {upper_bound:.2f} (Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f})")

    # Filter outliers
    df = df[(df['price_per_gram'] >= lower_bound) & (df['price_per_gram'] <= upper_bound)]

    return df

def getParamsForRanking(df: pd.DataFrame) -> tuple:
    """
    Get parameters for Bayesian rating calculation.

    m = Global average rating (baseline rating)
    C = Median review count (confidence threshold)

    Higher m → ratings regress toward average
    Lower m → individual ratings have more weight
    """
    m = round(df['Rating'].mean(), 2)  # Global average rating
    C = df['review_count'].quantile(0.50)  # Median review count (50th percentile)

    print(f"m (Global Avg rating) = {m}, C (50th percentile of Review Count) = {C}")
    return m, C

def enrichColumn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich DataFrame with calculated columns:
    - weighted_rating: Bayesian average rating
    - price_per_gram: Price normalized by weight
    """
    # Bayesian average rating
    # https://arpitbhayani.me/blogs/bayesian-average/
    m, c = getParamsForRanking(df)

    df['weighted_rating'] = (
        (df['review_count'] / (df['review_count'] + c)) * df['Rating'] +
        (c / (df['review_count'] + c)) * m
    ).round(2)

    # Calculate price per gram
    # Extract numeric value from Weight column (e.g., "500g" -> 500)
    if 'Weight' in df.columns:
        df['weight_grams'] = df['Weight'].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
        df['price_per_gram'] = (df['current_price'] / df['weight_grams']).round(2)
        df['price_per_gram'] = df['price_per_gram'].fillna(0)
    else:
        df['price_per_gram'] = 0

    # Sort by weighted rating descending
    df = df.sort_values('weighted_rating', ascending=False)

    return df

def get_price_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Categorize products into price segments based on price_per_gram"""
    print(f"\nPrice per gram statistics:\n{df['price_per_gram'].describe()}\n")

    # Calculate price range percentiles
    price_25 = df['price_per_gram'].quantile(0.25)
    price_50 = df['price_per_gram'].quantile(0.50)
    price_90 = df['price_per_gram'].quantile(0.90)

    # Create price segments
    conditions = [
        df['price_per_gram'] <= price_25,
        (df['price_per_gram'] > price_25) & (df['price_per_gram'] <= price_50),
        (df['price_per_gram'] > price_50) & (df['price_per_gram'] <= price_90),
        df['price_per_gram'] > price_90
    ]

    choices = ['Budget', 'Mid-Range', 'Premium', 'Luxury']

    df['price_segment'] = np.select(conditions, choices, default='Unknown')

    # Rename column if not already done
    if 'Current Price' in df.columns:
        df = df.rename(columns={"Current Price": "current_price"})

    return df

def get_insights_of_brand(df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate brand-level insights with Bayesian rating and trust scores.

    Returns DataFrame with:
    - product_count: Number of products per brand
    - avg_review_count: Average reviews per product
    - avg_rating: Average weighted rating
    - brand_rating: Bayesian-adjusted brand rating
    - confidence_level: 1 (high), 2 (medium), 3 (low)
    - trust_score: Percentage confidence (0-100)
    - brand_rank: Overall ranking
    """
    m, C = getParamsForRanking(df)
    print(f"Global Avg rating (m) = {m}, Global Review count (C) = {C}")

    # Filter out unknown brands and group
    brand_agg = df[df['Brand'] != 'Unknown'].groupby('Brand').agg({
        'Brand': 'count',  # Product count
        'review_count': 'mean',
        'weighted_rating': 'mean'
    }).rename(columns={
        'Brand': 'product_count',
        'review_count': 'avg_review_count',
        'weighted_rating': 'avg_rating'
    }).round(2)

    # Calculate Bayesian average rating for brands
    brand_agg['brand_rating'] = (
        (brand_agg['avg_review_count'] / (brand_agg['avg_review_count'] + C)) * brand_agg['avg_rating'] +
        (C / (brand_agg['avg_review_count'] + C)) * m
    ).round(2)

    # Assign confidence levels
    conditions = [
        brand_agg['avg_review_count'] >= 2 * C,
        brand_agg['avg_review_count'] >= C,
        brand_agg['avg_review_count'] < C
    ]
    choices = ['1', '2', '3']
    brand_agg['confidence_level'] = np.select(conditions, choices, default='3')

    # Calculate trust score (0-100%)
    brand_agg['trust_score'] = (
        (brand_agg['avg_review_count'] / (C + brand_agg['avg_review_count'])) * 100
    ).round(2)

    # Sort by brand_rating, trust_score, confidence_level
    brand_agg = brand_agg.sort_values(
        by=['brand_rating', 'trust_score', 'confidence_level'],
        ascending=[False, False, True]
    )

    # Add brand rank using dense ranking
    brand_agg['brand_rank'] = brand_agg['brand_rating'].rank(method='dense', ascending=False).astype(int)

    # Reset index to make Brand a column
    brand_agg = brand_agg.reset_index()

    print(f"\nTop 20 Brands:\n{brand_agg.head(20)}\n")

    return brand_agg

def main(input_path=None, review_path=None, search_id=None):
    """
    Main data pipeline function. Processes data and uploads to R2.
    Pandas-based implementation - optimized for KB-sized datasets.

    Args:
        input_path: Path to input CSV (local temp file)
        review_path: Path to review CSV (local temp file)
        search_id: Search UUID (required for R2 upload)
    """
    if not search_id:
        raise ValueError("search_id is required for R2 upload")

    if input_path:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        # Load product data
        print(f"Loading data from: {input_path}")
        df = load_data(input_path, "csv")

        print("Checking data quality...")
        quality_passed = check_data_quality(df)
        result_file_name = input_path.split("/")[-1].replace(".csv", "_cleaned.csv")

        if quality_passed:
            print("✓ Data quality checks passed.")

            # Data processing pipeline
            print("Cleaning data...")
            data_cleaned = apply_data_cleaning(df)

            print("Enriching columns...")
            enriched_df = enrichColumn(data_cleaned)

            print("Removing outliers...")
            advanced_cleaned = apply_advanced_cleaning(enriched_df)

            print("Calculating price segments...")
            enriched_df = get_price_segment(advanced_cleaned)

            # Sort by price per gram descending
            enriched_df = enriched_df.sort_values('price_per_gram', ascending=False)

            # Upload silver data to R2
            print(f"\nUploading silver data to R2 for search_id: {search_id}")
            silver_path = storage.upload_silver_data(
                df=enriched_df,
                search_id=search_id,
                filename=result_file_name,
                df_type='pandas'
            )

            if silver_path:
                print(f"✓ Silver data uploaded to R2: {silver_path}")
            else:
                print("✗ Failed to upload silver data to R2")

            # Generate and upload brand insights to R2
            print("\nGenerating brand insights...")
            brand_insight = get_insights_of_brand(enriched_df)

            print(f"Uploading brand insights to R2 for search_id: {search_id}")
            brand_path = storage.upload_brand_insights(
                df=brand_insight,
                search_id=search_id,
                filename=result_file_name,
                df_type='pandas'
            )

            if brand_path:
                print(f"✓ Brand insights uploaded to R2: {brand_path}")
            else:
                print("✗ Failed to upload brand insights to R2")

        else:
            print("✗ Data quality checks failed.")
            # Update database to mark data quality as failed
            if search_id:
                from backend.services.db_services import DatabaseService as DBService
                from backend.database.database import SessionLocal
                db = SessionLocal()
                try:
                    DBService.update_data_quality_passed(db, search_id, False)
                    print(f"Updated data_quality_passed to False for search_id: {search_id}")
                except Exception as e:
                    print(f"Error updating data quality status: {e}")
                finally:
                    db.close()
            raise ValueError("Data quality checks failed. Cannot generate insights.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        review_path = sys.argv[2] if len(sys.argv) > 2 else None
        search_id = sys.argv[3] if len(sys.argv) > 3 else None
        main(input_path, review_path, search_id)
    else:
        print("Usage: python data_engg_v2.py <input_path> [review_path] [search_id]")
