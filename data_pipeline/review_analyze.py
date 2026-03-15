#Quality check
#Cleaning
#Ranking Brand
#Ranking Products
# Q - Where to store review data?
# # A - Review data should be stored in a dedicated reviews table or collection within the database. This allows for efficient querying and analysis of reviews separately from product data. Each review entry should include fields such as product_id (to link to the product), user_id (if applicable), rating, review_text, date_posted, and any other relevant metadata. This structure facilitates better management of review data and supports features like filtering, sorting, and aggregating reviews for insights.

import sys
import os
from dotenv import load_dotenv
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, when, lit, count, avg, sum, dense_rank, coalesce, split, trim, upper, percentile_approx
from pyspark.sql import Window
from pyspark.sql.functions import udf, collect_list, pandas_udf, PandasUDFType
from pyspark.sql.types import StringType, IntegerType, MapType, StructType, StructField, DoubleType
import pandas as pd
from pyspark.sql.functions import udf, col

# Load environment variables from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))


from data_pipeline.ReviewAnalyzer import ClaudeReviewSummarizer
class Config:
    APP_NAME = "EcommerceScraper"
    MASTER = "local[*]"
    DATA_PATH = "./data/"
    LOG_LEVEL = "INFO"

def create_spark_session(app_name: str = Config.APP_NAME, master: str = Config.MASTER) -> SparkSession:   
    """Create and return a Spark session"""
    spark = SparkSession.builder \
        .appName(app_name) \
        .master(master) \
        .config("spark.driver.memory", "2g") \
        .getOrCreate()
    return spark

def load_data(spark: SparkSession, file_path: str, file_format: str = "csv"):
    """Load data from CSV file into Spark DataFrame"""
    if file_format == "csv":
        df = spark.read.option("header", "true").option("inferSchema", "true").csv(file_path)
    elif file_format == "json":
        df = spark.read.json(file_path)
    elif file_format == "parquet":
        df = spark.read.parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
    return df

def save_data(df, file_path: str, file_format: str = "csv"):
    """Save Spark DataFrame to specified file format"""
    if file_format == "csv":
        df.write.mode("overwrite").option("header", "true").csv(file_path)
    elif file_format == "json":
        df.write.mode("overwrite").json(file_path)
    elif file_format == "parquet":
        df.write.mode("overwrite").parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_format}")
    
"""Check data quality"""
def check_data_quality(df) -> bool:
    """Check if DataFrame meets basic quality checks"""
    if df is None or df.count() == 0:
        return False
    
    rows = df.count()
    
    # Check for nulls in critical columns (example: 'name', 'cur_price')
    critical_columns = ['name', 'cur_price']
    for col in critical_columns:
        if col in df.columns:
            null_count = df.filter(df[col].isNull()).count()
            if null_count > 0:
                return False
    
    #If following column is empty for more than 50% of rows, fail quality check
    optional_columns = ['rating', 'review_count', 'brand']
    for col in optional_columns:
        if col in df.columns:
            null_count = df.filter(df[col].isNull()).count()
            if null_count > rows * 0.5:
                return False

    return True

def apply_data_cleaning(df):
    df = df.dropDuplicates()
    df = df.fillna({'Rating': 0, 'Review Count': 0, 'Brand': 'Unknown', 'Country of Origin': 'Unknown'})

    text_columns = ["Product Name", "Brand", "Country of Origin"]
    for col_name in text_columns:
        if col_name in df.columns:
            df = df.withColumn(col_name, trim(col(col_name)))
    
    #capitalze columns
    capital_columns = ["Brand", "Country of Origin"]
    for col_name in capital_columns:
        if col_name in df.columns:
            df = df.withColumn(col_name, upper(col(col_name)))
    
    numeric_columns = ["Current Price", "Rating", "Review Count"]
    for col_name in numeric_columns:
        if col_name in df.columns:
            df = df.withColumn(col_name, when(col(col_name) < 0, 0).otherwise(col(col_name)))

    return df

def apply_advanced_cleaning(df):
    # Remove outliers using IQR (Interquartile Range) method
    # This method only removes statistically significant outliers, not just top/bottom percentages
    q1, q3 = df.approxQuantile("price_per_gram", [0.25, 0.75], 0.0)
    iqr = q3 - q1

    # Using 1.5 * IQR for outlier detection (standard approach)
    # For more extreme outliers only, use 3 * IQR
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    print(f"Price per gram outlier bounds: {lower_bound:.2f} to {upper_bound:.2f} (Q1={q1:.2f}, Q3={q3:.2f}, IQR={iqr:.2f})")
    df = df.filter((col("price_per_gram") >= lower_bound) & (col("price_per_gram") <= upper_bound))

    return df



def getParamsForRanking(df):
    #m = how many reviews are needed before you “trust” a product’s rating
    #Small m → new products surface faster
    #Large m → only established products dominate
    # So m is NOT a math parameter — it’s a market maturity parameter.
    # C = df.approxQuantile("Review Count", [0.50], 0.0) #Returned list
    #higher m implies it reaches more toward average
    #lower m implies it relies more on individual rating

    global_stats = df.agg(
    round(avg(col("Rating")), 2).alias("Global Avg rating"),
    percentile_approx("Review Count", [0.50])[0].alias("Global Review count")
    # avg(col("Review Count")).alias("Global Review count")
    ).collect()[0]
    m = global_stats["Global Avg rating"]
    C = global_stats["Global Review count"]
    print(f"m (50th percentile of Review Count) = {C}, Global Avg rating = {m}")
    return m, C

def enrichColumn(df):
    #bayesian average rating
    #https://arpitbhayani.me/blogs/bayesian-average/
    m, c = getParamsForRanking(df)
    def weighted_rating(rating, review_count):
        return (((review_count / (review_count + c)) * rating) + ((c / (review_count + c)) * m))
    df = df.withColumn("weighted_rating", round(weighted_rating(col("Rating"), col("Review Count")), 2))

    #deprecating this since weight columns is not always correct
    df = df.withColumn("price_per_gram", coalesce(round(col("Current Price") / split(col("Weight"), "g")[0].cast("double") , 2), lit(0)))
    return df.orderBy(col("weighted_rating").desc())

def get_price_segment(df):
    price_range = df.approxQuantile("price_per_gram", [0.25, 0.5, 0.9], 0.0)
    df = df.withColumn("price_segment", when((col("price_per_gram") <= price_range[0]), lit("Budget"))
                       .when((col("price_per_gram") <= price_range[1]), lit("Mid-Range"))
                          .when((col("price_per_gram") <= price_range[2]), lit("Premium"))
                            .otherwise(lit("Luxury")))
    return df



def get_insights_of_brand(df):
    #top brands with average rating rounded at 2 decimal places
    # global_stats = df.agg(
    #     round(avg(col("weighted_rating")), 2).alias("Global Avg rating"),
    #     avg(col("Review Count")).alias("Global Review count")
    # ).collect()[0]
    # m = global_stats["Global Avg rating"]
    # C = global_stats["Global Review count"]
    m, C = getParamsForRanking(df)
    print(f"Global Avg rating (m) = {m}, Global Review count (C) = {C}")
    brand_agg = df.filter(col("Brand") != "Unknown").groupBy("Brand") \
        .agg(count("*").alias("product_count"),
             round(avg(col("Review Count")), 2).alias("avg_review_count"),
             round(avg(col("weighted_rating")), 2).alias("avg_rating"))
    # Bayesian average rating for brands
    result = brand_agg.withColumn("brand_rating", 
                                     round((col("avg_review_count") / (col("avg_review_count") + C)) * col("avg_rating") + 
                                           (C / (col("avg_review_count") + C)) * m, 2)).orderBy(col("brand_rating").desc()) \
                        .withColumn("confidence_level", 
                                    when(col("avg_review_count") >= 2*C, lit("1"))
                                    .when(col("avg_review_count") >= C, lit("2"))
                                    .otherwise(lit("3")) 
                        ) \
                        .withColumn("trust_score", round((col("avg_review_count")/(C + col("avg_review_count")))*100, 2))
    windowSpec = Window.orderBy(col("brand_rating").desc(), col("trust_score").desc(), col("confidence_level"))
    result = result.withColumn("brand_rank", dense_rank().over(windowSpec))
  
    result.show(20, False)
    return result

# Define the schema for the Pandas UDF output
summary_output_schema = StructType([
    StructField("overall_sentiment", StringType(), True),
    StructField("summary", StringType(), True),
    StructField("taste_rating", DoubleType(), True),
    StructField("quality_rating", DoubleType(), True),
    StructField("price_rating", DoubleType(), True),
    StructField("packaging_rating", DoubleType(), True)

])

def main(input_path=None, review_path=None, search_id=None):
    """
    Main review analysis function. Processes reviews and uploads to R2.

    Args:
        input_path: Path to input CSV (local temp file)
        review_path: Path to review CSV (local temp file)
        search_id: Search UUID (optional, for R2 upload)
    """
    spark = create_spark_session()

    # Example usage
    if input_path:
        #product_Details    
        df = load_data(spark, input_path, "csv")
        print("checking data quality")
        quality_passed = check_data_quality(df)
        import pandas as pd
        from data_pipeline.ReviewAnalyzer import ClaudeReviewSummarizer
        
        # Read with Pandas
        print(f"Reading reviews from: {review_path}")
        reviews_df = pd.read_csv(review_path)
        
        # Group reviews
        grouped = reviews_df.groupby('name')['reviews'].apply(list).reset_index()
        grouped['review_count'] = reviews_df.groupby('name').size().values
        
        print(f"Found {len(grouped)} products\n")
        
        # Initialize Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        summarizer = ClaudeReviewSummarizer(api_key=api_key)
        
        # Process each product
        results = []
        for idx, row in grouped.iterrows():
            product_name = row['name']
            reviews = row['reviews']
            review_count = row['review_count']
            
            try:
                summary = summarizer.generate_summary(reviews, product_name)
                aspect_ratings = summary.get('aspect_ratings', {})
                
                result = {
                    'name': product_name,
                    'review_count': review_count,
                    'overall_sentiment': summary.get('overall_sentiment', ''),
                    'summary': summary.get('summary', ''),
                    'taste': aspect_ratings.get('taste'),
                    'quality': aspect_ratings.get('quality'),
                    'price': aspect_ratings.get('price'),
                    'packaging': aspect_ratings.get('packaging')
                }
                results.append(result)
                print(f"  ✓ Done\n")
                
            except Exception as e:
                print(f"  ✗ Error: {e}\n")
                results.append({
                    'name': product_name,
                    'review_count': review_count,
                    'overall_sentiment': 'error',
                    'summary': str(e),
                    'taste': None,
                    'quality': None,
                    'price': None,
                    'packaging': None
                })
        
        # Save results
        results_df = pd.DataFrame(results)
        results_df[['taste', 'quality', 'price', 'packaging', 'summary', 'overall_sentiment']].fillna('', inplace=True)
        review_analysis_file_name = review_path.split("/")[-1].replace(".csv", "_analysis.csv")

        # Upload to R2 if search_id provided
        if search_id:
            from backend.storage.r2_storage import get_storage
            storage = get_storage()

            print(f"Uploading review analysis to R2 for search_id: {search_id}")
            review_path_r2 = storage.upload_review_analysis(
                df=results_df,
                search_id=search_id,
                filename=review_analysis_file_name,
                df_type='pandas'
            )

            if review_path_r2:
                print(f"✓ Review analysis uploaded to R2: {review_path_r2}")
            else:
                print("✗ Failed to upload review analysis to R2")
        else:
            # Fallback to local storage if no search_id
            review_analysis_file_path = "/Users/mw-sanskar/Documents/sanskar/projects/EcommerceScrapper/final_result/review_analysis/" + review_analysis_file_name
            results_df.to_csv(review_analysis_file_path, index=False)
            print(f"Saved to local: {review_analysis_file_path}")

        print(results_df.head(2))

    spark.stop()


if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        review_path = sys.argv[2] if len(sys.argv) > 2 else None
        main(input_path, review_path)
    else:
        print("Please provide input file path as argument.")

