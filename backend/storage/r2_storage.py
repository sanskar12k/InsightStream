# storage/r2_storage.py
"""
Cloudflare R2 storage manager for CSV files
"""

import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv
import logging
import io

load_dotenv()
logger = logging.getLogger(__name__)

class R2Storage:
    """Manage file storage in Cloudflare R2"""
    
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=os.getenv('R2_ENDPOINT_URL'),
            aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
            region_name=os.getenv('R2_REGION', 'auto')
        )
        self.bucket_name = os.getenv('R2_BUCKET_NAME')
    
    def upload_file(self, local_path: str, remote_path: str, metadata: dict = None) -> bool:
        """
        Upload file to R2
        
        Args:
            local_path: Path to local file
            remote_path: Path in R2 bucket (e.g., 'user_123/search_456/products.csv')
            metadata: Optional metadata dict
        
        Returns:
            True if successful
        """
        try:
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            logger.info(f"Uploading {local_path} to R2://{self.bucket_name}/{remote_path}")
            
            self.client.upload_file(
                Filename=local_path,
                Bucket=self.bucket_name,
                Key=remote_path,
                ExtraArgs=extra_args
            )
            
            logger.info(f"✓ Upload successful: {remote_path}")
            return True
            
        except ClientError as e:
            logger.error(f"✗ Upload failed: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from R2"""
        try:
            logger.info(f"Downloading R2://{self.bucket_name}/{remote_path} to {local_path}")
            
            # Create directory if needed
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.client.download_file(
                Bucket=self.bucket_name,
                Key=remote_path,
                Filename=local_path
            )
            
            logger.info(f"✓ Download successful: {local_path}")
            return True
            
        except ClientError as e:
            logger.error(f"✗ Download failed: {e}")
            return False

    def get_spark_config(self) -> dict:
        """
        Get Spark configuration for R2 access

        Returns:
            Dict of Spark configuration settings to enable direct R2 writes

        Usage:
            spark_config = storage.get_spark_config()
            spark = SparkSession.builder.config(map=spark_config).getOrCreate()

        """
        return {
            "spark.hadoop.fs.s3a.endpoint": os.getenv('R2_ENDPOINT_URL'),
            "spark.hadoop.fs.s3a.access.key": os.getenv('R2_ACCESS_KEY_ID'),
            "spark.hadoop.fs.s3a.secret.key": os.getenv('R2_SECRET_ACCESS_KEY'),
            "spark.hadoop.fs.s3a.path.style.access": "true",
            "spark.hadoop.fs.s3a.impl": "org.apache.hadoop.fs.s3a.S3AFileSystem",
            "spark.hadoop.fs.s3a.aws.credentials.provider": "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
            # R2-specific configurations
            "spark.hadoop.fs.s3a.connection.ssl.enabled": "true",
            "spark.hadoop.fs.s3a.attempts.maximum": "3",
            "spark.hadoop.fs.s3a.connection.establish.timeout": "5000",
            "spark.hadoop.fs.s3a.connection.timeout": "200000",
            # Disable features not supported by R2
            "spark.hadoop.fs.s3a.bucket.probe": "0",
            "spark.hadoop.fs.s3a.change.detection.version.required": "false",
            "spark.hadoop.fs.s3a.change.detection.mode": "none"
        }

    def upload_spark_dataframe(self, df, remote_path: str, mode: str = 'overwrite',
                              coalesce: int = 1) -> bool:
        """
        Upload Spark DataFrame directly to R2 using native Spark write

        Args:
            df: Spark DataFrame
            remote_path: Path in R2 bucket (e.g., 'user_123/search_456/products.csv')
            mode: Write mode ('overwrite', 'append', 'ignore', 'error')
            coalesce: Number of output files (default 1 for single CSV)

        Returns:
            True if successful

        Note:
            - Ensure Spark session has R2 config (use get_spark_config())
            - If coalesce=1, output will be in a folder with part-00000-*.csv
            - For single CSV file, you may need to handle the part file naming
        """
        try:
            s3_path = f"s3a://{self.bucket_name}/{remote_path}"
            logger.info(f"Writing Spark DataFrame to {s3_path}")

            df.coalesce(coalesce).write.mode(mode).csv(
                s3_path,
                header=True
            )

            logger.info(f"✓ Spark DataFrame write successful: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"✗ Spark DataFrame write failed: {e}")
            return False

    def upload_pandas_dataframe(self, df, remote_path: str, metadata: dict = None) -> bool:
        """
        Upload pandas DataFrame directly to R2 without writing to local file

        Args:
            df: pandas DataFrame
            remote_path: Path in R2 bucket (e.g., 'user_123/search_456/products.csv')
            metadata: Optional metadata dict

        Returns:
            True if successful
        """
        try:
            # Convert DataFrame to CSV in memory
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata

            logger.info(f"Uploading pandas DataFrame to R2://{self.bucket_name}/{remote_path}")

            # Upload from memory
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=remote_path,
                Body=csv_data.encode('utf-8'),
                ContentType='text/csv',
                **extra_args
            )

            logger.info(f"✓ pandas DataFrame upload successful: {remote_path}")
            return True

        except Exception as e:
            logger.error(f"✗ pandas DataFrame upload failed: {e}")
            return False

    def upload_dataframe_csv(self, df, user_id: str, search_id: str,
                            platform: str, file_type: str = 'products',
                            df_type: str = 'pandas', **kwargs) -> Optional[str]:
        """
        Upload DataFrame with organized folder structure (no local file needed)

        Args:
            df: pandas DataFrame or Spark DataFrame
            user_id: User UUID
            search_id: Search UUID
            platform: 'amazon' or 'flipkart'
            file_type: 'products' or 'reviews'
            df_type: 'pandas' or 'spark' (default: 'pandas')
            **kwargs: Additional args passed to respective upload method
                     (e.g., mode='overwrite', coalesce=1 for Spark)

        Returns:
            Remote path if successful, None otherwise
        """
        # Organized structure: user_id/search_id/platform_filetype.csv
        remote_path = f"{user_id}/{search_id}/{platform}_{file_type}.csv"

        metadata = {
            'user_id': user_id,
            'search_id': search_id,
            'platform': platform,
            'file_type': file_type
        }

        if df_type == 'spark':
            success = self.upload_spark_dataframe(df, remote_path, **kwargs)
        else:
            success = self.upload_pandas_dataframe(df, remote_path, metadata)

        return remote_path if success else None

    def upload_csv(self, local_path: str, user_id: str, search_id: str, 
                   platform: str, file_type: str = 'products') -> Optional[str]:
        """
        Upload CSV with organized folder structure
        
        Args:
            local_path: Path to CSV file
            user_id: User UUID
            search_id: Search UUID
            platform: 'amazon' or 'flipkart'
            file_type: 'products' or 'reviews'
        
        Returns:
            Remote path if successful, None otherwise
        """
        # Organized structure: user_id/search_id/platform_filetype.csv
        remote_path = f"{user_id}/{search_id}/{platform}_{file_type}.csv"
        
        metadata = {
            'user_id': user_id,
            'search_id': search_id,
            'platform': platform,
            'file_type': file_type
        }
        
        success = self.upload_file(local_path, remote_path, metadata)
        return remote_path if success else None
    
    def list_files(self, prefix: str = '') -> list:
        """List files in bucket with optional prefix"""
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' not in response:
                return []
            
            files = [obj['Key'] for obj in response['Contents']]
            logger.info(f"Found {len(files)} files with prefix '{prefix}'")
            return files
            
        except ClientError as e:
            logger.error(f"✗ List failed: {e}")
            return []
    
    def delete_file(self, remote_path: str) -> bool:
        """Delete file from R2"""
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )
            logger.info(f"✓ Deleted: {remote_path}")
            return True
            
        except ClientError as e:
            logger.error(f"✗ Delete failed: {e}")
            return False
    
    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate presigned URL for temporary file access
        
        Args:
            remote_path: Path in R2
            expires_in: URL expiration in seconds (default 1 hour)
        
        Returns:
            Presigned URL or None
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': remote_path
                },
                ExpiresIn=expires_in
            )
            logger.info(f"Generated URL for {remote_path} (expires in {expires_in}s)")
            return url
            
        except ClientError as e:
            logger.error(f"✗ URL generation failed: {e}")
            return None
    
    def get_bucket_size(self) -> dict:
        """Get total bucket size and file count"""
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name)

            if 'Contents' not in response:
                return {'total_size': 0, 'file_count': 0}

            total_size = sum(obj['Size'] for obj in response['Contents'])
            file_count = len(response['Contents'])

            return {
                'total_size': total_size,
                'total_size_mb': round(total_size / 1024 / 1024, 2),
                'file_count': file_count
            }

        except ClientError as e:
            logger.error(f"✗ Size calculation failed: {e}")
            return {'total_size': 0, 'file_count': 0}

    def read_csv_to_dataframe(self, remote_path: str, encoding: str = 'utf-8'):
        """
        Read CSV from R2 directly into pandas DataFrame

        Args:
            remote_path: Path to CSV file in R2
            encoding: File encoding (default: utf-8)

        Returns:
            pandas DataFrame or None if failed
        """
        try:
            import pandas as pd

            logger.info(f"Reading CSV from R2://{self.bucket_name}/{remote_path}")

            # Get object from R2
            response = self.client.get_object(
                Bucket=self.bucket_name,
                Key=remote_path
            )

            # Read CSV from response body
            csv_content = response['Body'].read()
            df = pd.read_csv(io.BytesIO(csv_content), encoding=encoding)

            logger.info(f"✓ Successfully read {len(df)} rows from {remote_path}")
            return df

        except UnicodeDecodeError:
            # Fallback to latin-1 encoding
            logger.warning(f"UTF-8 decode failed, trying latin-1 for {remote_path}")
            try:
                response = self.client.get_object(
                    Bucket=self.bucket_name,
                    Key=remote_path
                )
                csv_content = response['Body'].read()
                df = pd.read_csv(io.BytesIO(csv_content), encoding='latin-1')
                logger.info(f"✓ Successfully read {len(df)} rows with latin-1 encoding")
                return df
            except Exception as e:
                logger.error(f"✗ Failed to read with latin-1: {e}")
                return None

        except Exception as e:
            logger.error(f"✗ Failed to read CSV: {e}")
            return None

    # ========== Specialized Methods for Data Types ==========

    def upload_scraping_results(self, product_df, review_df, search_id: str,
                               product_name: str, timestamp: str,
                               df_type: str = 'pandas') -> dict:
        """
        Upload scraping results (products and reviews) to R2

        Folder structure: {search_id}/scraping/{filename}.csv

        Args:
            product_df: DataFrame with product data
            review_df: DataFrame with review data
            search_id: Search UUID
            product_name: Product search term
            timestamp: Timestamp string (e.g., '20260313_165622')
            df_type: 'pandas' or 'spark'

        Returns:
            Dict with paths: {'products': 'path', 'reviews': 'path'}
        """
        paths = {}

        # Upload products
        product_path = f"{search_id}/scraping/{product_name}_{timestamp}.csv"
        metadata = {
            'search_id': search_id,
            'data_type': 'scraping_results',
            'file_type': 'products',
            'product_name': product_name,
            'timestamp': timestamp
        }

        if df_type == 'spark':
            success = self.upload_spark_dataframe(product_df, product_path, mode='overwrite', coalesce=1)
        else:
            success = self.upload_pandas_dataframe(product_df, product_path, metadata)

        paths['products'] = product_path if success else None

        # Upload reviews
        review_path = f"{search_id}/scraping/{product_name}_reviews_{timestamp}.csv"
        metadata['file_type'] = 'reviews'

        if df_type == 'spark':
            success = self.upload_spark_dataframe(review_df, review_path, mode='overwrite', coalesce=1)
        else:
            success = self.upload_pandas_dataframe(review_df, review_path, metadata)

        paths['reviews'] = review_path if success else None

        logger.info(f"✓ Uploaded scraping results for search {search_id}: {paths}")
        return paths

    def upload_silver_data(self, df, search_id: str, filename: str,
                          df_type: str = 'spark') -> Optional[str]:
        """
        Upload silver (cleaned) data to R2

        Folder structure: {search_id}/silver/{filename}/

        Args:
            df: DataFrame with cleaned product data
            search_id: Search UUID
            filename: Base filename (e.g., 'millet_snacks_20260313_145516_cleaned.csv')
            df_type: 'pandas' or 'spark' (default: spark)

        Returns:
            Remote path if successful, None otherwise
        """
        # For Spark, use directory structure to match Spark output
        remote_path = f"{search_id}/silver/{filename}"

        metadata = {
            'search_id': search_id,
            'data_type': 'silver_data',
            'filename': filename
        }

        if df_type == 'spark':
            # Spark writes with quote options
            try:
                s3_path = f"s3a://{self.bucket_name}/{remote_path}"
                logger.info(f"Writing silver data to {s3_path}")

                df.coalesce(1).write \
                    .option("header", "true") \
                    .option("quote", '"') \
                    .option("escape", '"') \
                    .option("quoteAll", "true") \
                    .mode("overwrite") \
                    .csv(s3_path)

                logger.info(f"✓ Silver data upload successful: {remote_path}")
                return remote_path
            except Exception as e:
                logger.error(f"✗ Silver data upload failed: {e}")
                return None
        else:
            success = self.upload_pandas_dataframe(df, remote_path, metadata)
            return remote_path if success else None

    def upload_brand_insights(self, df, search_id: str, filename: str,
                             df_type: str = 'spark') -> Optional[str]:
        """
        Upload brand insights to R2

        Folder structure: {search_id}/brand_insight/{filename}/

        Args:
            df: DataFrame with brand analytics
            search_id: Search UUID
            filename: Base filename (e.g., 'millet_snacks_20260313_145516_cleaned.csv')
            df_type: 'pandas' or 'spark' (default: spark)

        Returns:
            Remote path if successful, None otherwise
        """
        remote_path = f"{search_id}/brand_insight/{filename}"

        metadata = {
            'search_id': search_id,
            'data_type': 'brand_insights',
            'filename': filename
        }

        if df_type == 'spark':
            try:
                s3_path = f"s3a://{self.bucket_name}/{remote_path}"
                logger.info(f"Writing brand insights to {s3_path}")

                df.write \
                    .option("header", "true") \
                    .option("quote", '"') \
                    .option("escape", '"') \
                    .option("quoteAll", "true") \
                    .mode("overwrite") \
                    .csv(s3_path)

                logger.info(f"✓ Brand insights upload successful: {remote_path}")
                return remote_path
            except Exception as e:
                logger.error(f"✗ Brand insights upload failed: {e}")
                return None
        else:
            success = self.upload_pandas_dataframe(df, remote_path, metadata)
            return remote_path if success else None

    def upload_review_analysis(self, df, search_id: str, filename: str,
                              df_type: str = 'pandas') -> Optional[str]:
        """
        Upload review analysis to R2

        Folder structure: {search_id}/review_analysis/{filename}.csv

        Args:
            df: DataFrame with review analysis
            search_id: Search UUID
            filename: Filename (e.g., 'millet_snacks_reviews_20260313_165622_analysis.csv')
            df_type: 'pandas' or 'spark' (default: pandas)

        Returns:
            Remote path if successful, None otherwise
        """
        remote_path = f"{search_id}/review_analysis/{filename}"

        metadata = {
            'search_id': search_id,
            'data_type': 'review_analysis',
            'filename': filename
        }

        if df_type == 'spark':
            success = self.upload_spark_dataframe(df, remote_path, mode='overwrite', coalesce=1)
        else:
            success = self.upload_pandas_dataframe(df, remote_path, metadata)

        return remote_path if success else None

    def get_scraping_results(self, search_id: str, file_type: str = 'products'):
        """
        Get scraping results DataFrame from R2

        Args:
            search_id: Search UUID
            file_type: 'products' or 'reviews'

        Returns:
            pandas DataFrame or None
        """
        # List files in scraping directory
        prefix = f"{search_id}/scraping/"
        files = self.list_files(prefix)

        # Filter by file type
        if file_type == 'products':
            csv_files = [f for f in files if '_reviews_' not in f and f.endswith('.csv')]
        else:
            csv_files = [f for f in files if '_reviews_' in f and f.endswith('.csv')]

        if not csv_files:
            logger.warning(f"No {file_type} files found in {prefix}")
            return None

        # Use the first matching file (most recent based on timestamp in filename)
        csv_files.sort(reverse=True)
        return self.read_csv_to_dataframe(csv_files[0])

    def get_silver_data(self, search_id: str):
        """
        Get silver data DataFrame from R2

        Args:
            search_id: Search UUID

        Returns:
            pandas DataFrame or None
        """
        prefix = f"{search_id}/silver/"
        files = self.list_files(prefix)

        # Find CSV files (could be in a Spark directory with part-00000 files)
        csv_files = [f for f in files if f.endswith('.csv') and 'part-' in f]

        if not csv_files:
            logger.warning(f"No silver data files found in {prefix}")
            return None

        # Use the first part file
        csv_files.sort()
        return self.read_csv_to_dataframe(csv_files[0])

    def get_brand_insights(self, search_id: str):
        """
        Get brand insights DataFrame from R2

        Args:
            search_id: Search UUID

        Returns:
            pandas DataFrame or None
        """
        prefix = f"{search_id}/brand_insight/"
        files = self.list_files(prefix)

        # Find CSV files
        csv_files = [f for f in files if f.endswith('.csv') and 'part-' in f]

        if not csv_files:
            logger.warning(f"No brand insight files found in {prefix}")
            return None

        csv_files.sort()
        return self.read_csv_to_dataframe(csv_files[0])

    def get_review_analysis(self, search_id: str):
        """
        Get review analysis DataFrame from R2

        Args:
            search_id: Search UUID

        Returns:
            pandas DataFrame or None
        """
        prefix = f"{search_id}/review_analysis/"
        files = self.list_files(prefix)

        # Find analysis CSV files
        csv_files = [f for f in files if f.endswith('_analysis.csv')]

        if not csv_files:
            logger.warning(f"No review analysis files found in {prefix}")
            return None

        csv_files.sort(reverse=True)
        return self.read_csv_to_dataframe(csv_files[0])


# Singleton instance
_storage = None

def get_storage() -> R2Storage:
    """Get singleton storage instance"""
    global _storage
    if _storage is None:
        _storage = R2Storage()
    return _storage