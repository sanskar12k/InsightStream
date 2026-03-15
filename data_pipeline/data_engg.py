#Quality check
#Cleaning
#Ranking Brand
#Ranking Products
# Q - Where to store review data?
# # A - Review data should be stored in a dedicated reviews table or collection within the database. This allows for efficient querying and analysis of reviews separately from product data. Each review entry should include fields such as product_id (to link to the product), user_id (if applicable), rating, review_text, date_posted, and any other relevant metadata. This structure facilitates better management of review data and supports features like filtering, sorting, and aggregating reviews for insights.

import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round, when, lit, count, avg, sum, dense_rank, coalesce, split, trim, upper, percentile_approx
from pyspark.sql import Window
from pyspark.sql.functions import udf, collect_list, pandas_udf, PandasUDFType
from pyspark.sql.types import StringType, IntegerType, MapType, StructType, StructField, DoubleType
import pandas as pd
from pyspark.sql.functions import udf, col

class Config:
    APP_NAME = "EcommerceScraper"
    MASTER = "local[*]"
    DATA_PATH = "./data/"
    LOG_LEVEL = "INFO"

def create_spark_session(app_name: str = Config.APP_NAME, master: str = Config.MASTER) -> SparkSession:
    """Create and return a Spark session with R2 configuration"""

    import os
    import shutil
    from backend.storage.r2_storage import get_storage

    # Ensure JAVA_HOME is set
    java_home = os.environ.get('JAVA_HOME')
    if not java_home:
        java_path = shutil.which('java')
        if java_path:
            java_home = os.path.dirname(os.path.dirname(java_path))
            os.environ['JAVA_HOME'] = java_home
            print(f"Setting JAVA_HOME to: {java_home}")

    # Stop any existing sessions
    try:
        SparkSession.getActiveSession().stop()
    except:
        pass

    # Get R2 configuration
    storage = get_storage()
    r2_config = storage.get_spark_config()

    # Build Spark session with R2 config
    builder = SparkSession.builder \
        .appName(app_name) \
        .master(master) \
        .config("spark.driver.memory", "2g") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.bindAddress", "127.0.0.1") \
        .config("spark.driver.host", "localhost") \
        .config("spark.ui.enabled", "false") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.367") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.sql.execution.arrow.pyspark.enabled", "false") \
        .config("spark.sql.execution.arrow.pyspark.fallback.enabled", "true") \
        .config("spark.python.worker.reuse", "true")

    # Add R2 configuration
    for key, value in r2_config.items():
        builder = builder.config(key, value)

    spark = builder.getOrCreate()
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

    return df.withColumnRenamed("Review Count", "review_count").withColumnRenamed("Current Price", "current_price")

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
    percentile_approx("review_count", [0.50])[0].alias("Global Review count")
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
    df = df.withColumn("weighted_rating", round(weighted_rating(col("Rating"), col("review_count")), 2))

    #deprecating this since weight columns is not always correct
    df = df.withColumn("price_per_gram", coalesce(round(col("current_price") / split(col("Weight"), "g")[0].cast("double") , 2), lit(0)))
    return df.orderBy(col("weighted_rating").desc())

def get_price_segment(df):
    df.show()
    price_range = df.approxQuantile("price_per_gram", [0.25, 0.5, 0.9], 0.0)
    df = df.withColumn("price_segment", when((col("price_per_gram") <= price_range[0]), lit("Budget"))
                       .when((col("price_per_gram") <= price_range[1]), lit("Mid-Range"))
                          .when((col("price_per_gram") <= price_range[2]), lit("Premium"))
                            .otherwise(lit("Luxury"))).withColumnRenamed("Current Price", "current_price")
        
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
             round(avg(col("review_count")), 2).alias("avg_review_count"),
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
    Main data pipeline function. Processes data and uploads to R2.

    Args:
        input_path: Path to input CSV (local temp file)
        review_path: Path to review CSV (local temp file)
        search_id: Search UUID (required for R2 upload)
    """
    spark = create_spark_session()

    if not search_id:
        raise ValueError("search_id is required for R2 upload")

    # Example usage
    if input_path:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        #product_Details
        df = load_data(spark, input_path, "csv")
        print("checking data quality")
        quality_passed = check_data_quality(df)
        result_file_name = input_path.split("/")[-1].replace(".csv", "_cleaned.csv")

        if quality_passed:
            print("Data quality checks passed.")
            data_cleaned = apply_data_cleaning(df)
            enriched_df = enrichColumn(data_cleaned)
            advanced_cleaned = apply_advanced_cleaning(enriched_df)
            enriched_df = get_price_segment(advanced_cleaned).orderBy(col("price_per_gram").desc())

            # Upload silver data to R2
            print(f"Uploading silver data to R2 for search_id: {search_id}")
            silver_path = storage.upload_silver_data(
                df=enriched_df,
                search_id=search_id,
                filename=result_file_name,
                df_type='spark'
            )

            if silver_path:
                print(f"✓ Silver data uploaded to R2: {silver_path}")
            else:
                print("✗ Failed to upload silver data to R2")

            # Generate and upload brand insights to R2
            brand_insight = get_insights_of_brand(enriched_df)
            print(f"Uploading brand insights to R2 for search_id: {search_id}")
            brand_path = storage.upload_brand_insights(
                df=brand_insight,
                search_id=search_id,
                filename=result_file_name,
                df_type='spark'
            )

            if brand_path:
                print(f"✓ Brand insights uploaded to R2: {brand_path}")
            else:
                print("✗ Failed to upload brand insights to R2")

        else:
            print("Data quality checks failed.")
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
            spark.stop()
            raise ValueError("Data quality checks failed. Cannot generate insights.")
    spark.stop()


if __name__ == "__main__":
    
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        review_path = sys.argv[2] if len(sys.argv) > 2 else None
        main(input_path, review_path)
    else:
        print("Please provide input file path as argument.")



                # analyzed_review = reviews_df.groupBy("name").agg(count("*").alias("review_count") ,collect_list("reviews").alias("reviews")).withColumn("review_summary", review_summarize_pandas_udf(col("name"), col("reviews")))
                # analyzed_review.show(truncate=False)
                # summarize_udf = udf(f=summarize_reviews, returnType=summary_output_schema)
                # summarize_udf = create_review_udf()
                # analyzed_review.withColumn("review_summary", summarize_udf(col("name"), col("reviews"))).show(truncate=False)
                # analyzed_review.show()
                # .write.option("header", True).mode("overwrite").parquet(intermediate_review_path)

                # result_df = spark.read.parquet(intermediate_review_path)

                # # Get the aspect ratings map for the first product
                # aspect_ratings_map = result_df.select(col("review_summary.aspect_ratings")).first()[0]

                # # Extract keys from the map
                # if aspect_ratings_map:
                #     aspect_keys = list(aspect_ratings_map.keys())
                # else:
                #     aspect_keys = []

                # print(f"Detected aspect keys: {aspect_keys}")

                # # Dynamically create select expressions for each aspect
                # select_expressions = [
                #     col("name"),
                #     col("review_count"),
                #     col("review_summary.overall_sentiment").alias("overall_sentiment"),
                #     col("review_summary.summary").alias("summary")
                # ]

                # for key in aspect_keys:
                #     select_expressions.append(col("review_summary.aspect_ratings").getItem(key).alias(f"{key}_rating"))

                # # Select the columns
                # df_aspect_ratings = result_df.select(*select_expressions)
                # df_aspect_ratings.show(truncate=False)
                # df_aspect_ratings.write.option("header", True).mode("overwrite").csv(output_path)