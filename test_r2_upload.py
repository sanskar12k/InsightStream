#!/usr/bin/env python3
"""
Simple test script to verify R2 DataFrame upload functionality
"""

import pandas as pd
from backend.storage.r2_storage import get_storage

def test_pandas_upload():
    """Test uploading pandas DataFrame to R2"""
    print("=" * 60)
    print("Testing Pandas DataFrame Upload to R2")
    print("=" * 60)

    # Create sample DataFrame
    df = pd.DataFrame({
        'product_name': ['iPhone 15', 'Samsung Galaxy S23', 'Google Pixel 8'],
        'price': [79999, 74999, 74999],
        'rating': [4.5, 4.3, 4.6],
        'reviews': [1200, 890, 650]
    })

    print("\nSample DataFrame:")
    print(df)

    # Initialize storage
    storage = get_storage()

    # Upload DataFrame
    print("\n📤 Uploading to R2...")
    remote_path = storage.upload_dataframe_csv(
        df=df,
        user_id='test_user_123',
        search_id='test_search_456',
        platform='amazon',
        file_type='products',
        df_type='pandas'
    )

    if remote_path:
        print(f"✅ Upload successful!")
        print(f"Remote path: {remote_path}")

        # Try to list the file
        print("\n📁 Listing files...")
        files = storage.list_files(prefix='test_user_123/test_search_456')
        print(f"Found {len(files)} files:")
        for f in files:
            print(f"  - {f}")

        # Generate presigned URL
        print("\n🔗 Generating download URL...")
        url = storage.get_file_url(remote_path, expires_in=3600)
        if url:
            print(f"✅ Download URL (expires in 1 hour):")
            print(f"  {url}")
        else:
            print("❌ Failed to generate URL")

    else:
        print("❌ Upload failed!")
        return False

    print("\n" + "=" * 60)
    return True


def test_spark_upload():
    """Test uploading Spark DataFrame to R2 (requires PySpark + hadoop-aws)"""
    print("=" * 60)
    print("Testing Spark DataFrame Upload to R2")
    print("=" * 60)

    try:
        from pyspark.sql import SparkSession
        from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType

        # Initialize storage
        storage = get_storage()

        # Create Spark session with R2 config
        print("\n🔧 Configuring Spark session...")
        spark_config = storage.get_spark_config()

        # Add S3A dependencies
        spark = SparkSession.builder \
            .appName("R2UploadTest") \
            .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
            .config(map=spark_config) \
            .getOrCreate()

        # Define explicit schema
        schema = StructType([
            StructField("product_name", StringType(), True),
            StructField("price", IntegerType(), True),
            StructField("rating", DoubleType(), True),
            StructField("reviews", IntegerType(), True)
        ])

        # Create sample DataFrame with explicit schema
        data = [
            ('iPhone 15', 79999, 4.5, 1200),
            ('Samsung Galaxy S23', 74999, 4.3, 890),
            ('Google Pixel 8', 74999, 4.6, 650)
        ]

        df = spark.createDataFrame(data, schema)

        print("\nSample Spark DataFrame:")
        df.show()

        # Upload DataFrame
        print("\n📤 Uploading to R2 via Spark...")
        remote_path = storage.upload_dataframe_csv(
            df=df,
            user_id='test_user_789',
            search_id='test_search_101',
            platform='flipkart',
            file_type='products',
            df_type='spark',
            mode='overwrite',
            coalesce=1
        )

        if remote_path:
            print(f"✅ Upload successful!")
            print(f"Remote path: {remote_path}")
        else:
            print("❌ Upload failed!")
            return False

        spark.stop()

    except ImportError:
        print("\n⚠️  PySpark not installed. Skipping Spark test.")
        print("Install with: pip install pyspark")
        return None
    except Exception as e:
        error_str = str(e)
        print(f"\n❌ Spark test failed: {e}")

        if "S3AFileSystem not found" in error_str or "hadoop-aws" in error_str:
            print("\n💡 Missing S3A connector. The Spark session is trying to download it.")
            print("   This requires internet connection and may take a moment.")
            print("   The JARs will be cached for future use.")

        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    return True


def cleanup_test_files():
    """Clean up test files from R2"""
    print("\n🧹 Cleaning up test files...")
    storage = get_storage()

    test_files = storage.list_files(prefix='test_user_')

    if test_files:
        print(f"Found {len(test_files)} test files to delete:")
        for file in test_files:
            print(f"  Deleting: {file}")
            if storage.delete_file(file):
                print(f"    ✅ Deleted")
            else:
                print(f"    ❌ Failed to delete")
    else:
        print("No test files to clean up.")


if __name__ == '__main__':
    print("\n🚀 Starting R2 Upload Tests\n")

    try:
        # Test pandas upload
        pandas_result = test_pandas_upload()

        # Test spark upload
        spark_result = test_spark_upload()

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Pandas Upload: {'✅ PASSED' if pandas_result else '❌ FAILED'}")
        if spark_result is not None:
            print(f"Spark Upload:  {'✅ PASSED' if spark_result else '❌ FAILED'}")
        else:
            print(f"Spark Upload:  ⚠️  SKIPPED (PySpark not installed)")
        print("=" * 60)

        # Ask to cleanup
        cleanup = input("\nDelete test files from R2? (y/n): ")
        if cleanup.lower() == 'y':
            cleanup_test_files()

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
