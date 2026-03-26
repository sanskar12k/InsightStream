from typing import List
from requests import Session
from backend.auth.jwt_auth import get_current_user, get_current_user_id
from backend.models.user_models import UserSearchHistoryRequest
from backend.database.database import SessionLocal, get_db
from backend.models.db_models import Status
from backend.models.scrapper_models import ScrappedData, ScrapperRequest, ScrapperResponse, ScrapperStatus, SearchStatistics
from fastapi import APIRouter,BackgroundTasks, HTTPException, status, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from backend.services.db_services import DatabaseService as DBService
import os
import pandas as pd
import numpy as np
import time

router = APIRouter(
    prefix="/scrapper",
    tags=["scrapper"],
    responses={404: {"description": "Not found"}},
)

def sanitize_csv_data(data_list):
    """
    Sanitize CSV data to ensure JSON compliance by converting
    NaN, Infinity, and -Infinity values to None.

    Args:
        data_list: List of dictionaries from pandas to_dict(orient='records')

    Returns:
        Sanitized list of dictionaries safe for JSON serialization
    """
    def sanitize_value(val):
        """Convert non-JSON-compliant values to None"""
        if val is None:
            return None
        if isinstance(val, float):
            if np.isnan(val) or np.isinf(val):
                return None
        return val

    return [
        {k: sanitize_value(v) for k, v in item.items()}
        for item in data_list
    ]

def start_scrapping(
        search_id: str,
        platform: list,
        product_name: str,
        category: str = None,
        deep_details: bool = True,
        max_products: int = 80,
        include_reviews: bool = False,
        auto_generate_insights: bool = False
):
    """
    Start the scrapping process for a given search ID and user ID.
    This function will be called in the background after creating a search record in the database.
    """
    from backend.models.db_models import Status
    print("starting the scrapping process for search_id:", search_id)
    db = SessionLocal()
    try:
        search_record = DBService.get_search_by_id(db, search_id)
        if not search_record:
            raise HTTPException(status_code=404, detail="Search record not found")

        # Update search status to in_progress
        DBService.update_search_status(db, search_id, Status.IN_PROGRESS)
        DBService.update_started_at(db, search_id)
        print("Search status updated to IN_PROGRESS for search_id:", search_id)
        # Call the ScraperOrchestrator to start scraping
        from  scrapping.ecommerce_scraper_backend import ScraperOrchestrator
        scraper = ScraperOrchestrator()
        print("ScraperOrchestrator initialized for search_id:", search_id)
        results = scraper.scrape_all(product_name, category, platform, max_products, deep_details, include_reviews)
        csv_data = scraper.export_to_csv_pandas(results, product=product_name.capitalize(), search_id=search_id)
        print("Scrapping completed and results exported to R2 for search_id:", search_id)

        # Count total products scraped across all platforms
        total_products =  0

        # Print detailed platform results
        print("Scraping Results:")
        for platform, data in results.items():
            print(f"Platform: {platform}")
            print(f"Success: {data['success']}")
            if data['success']:
                total_products += int(data['count'])

        # Update search status to completed
        # Store R2 paths in database (products path as main output path)
        output_path = csv_data.get('filename_structure') if csv_data else None
        DBService.update_output_path(db, search_id, output_path)
        DBService.update_total_products_scraped(db, search_id, total_products)
        DBService.update_search_status(db, search_id, Status.COMPLETED)
        DBService.update_completed_at(db, search_id)

        # Auto-generate insights if requested
        if auto_generate_insights and csv_data:
            print("Auto-generating insights for search_id:", search_id)
            try:
                generate_insights(search_id, csv_data.get('filename_structure'))
                DBService.update_insight_generated(db, search_id, True)
                print("Insights generated successfully for search_id:", search_id)
            except Exception as e:
                print(f"Error generating insights: {e}")
                # Don't fail the whole scraping if insights generation fails

    except Exception as e:
        # Update search status to failed in case of any exception
        print(f"Error during scrapping: {e}")
        DBService.update_search_status(db, search_id, Status.FAILED)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


#run data pipeline to generate insights and update the search record with insights data and insights file path

def generate_insights(
    search_id: str,
    output_file_name: str
):
    """
    Generate insights from the scrapped data in R2 for a given search ID.
    This function will be called after the scrapping process is completed to generate insights and update the search record with insights data and insights file path.
    """
    start_time = time.time()
    db = SessionLocal()
    try:
        from backend.storage.r2_storage import get_storage
        import data_pipeline.data_engg_v2 as generate_insights_module
        import data_pipeline.review_analyze_v2 as review_analyzer

        print(f"Generating insights for search_id: {search_id}")
        print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

        # Extract product name and timestamp from filename
        filename_without_ext = output_file_name.replace('.csv', '')
        parts = filename_without_ext.split("_")
        product_name = "_".join(parts[:-2])
        timestamp = "_".join(parts[-2:])
        print(f"Product: {product_name}, Timestamp: {timestamp}")

        # Get R2 storage instance
        storage = get_storage()

        # Read scraping results from R2
        product_df = storage.get_scraping_results(search_id, file_type='products')
        review_df = storage.get_scraping_results(search_id, file_type='reviews')

        if product_df is None or review_df is None:
            raise Exception("Failed to read scraping results from R2")

        # Create temporary files for the data pipeline (which expects file paths)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as product_temp:
            product_df.to_csv(product_temp.name, index=False, encoding='utf-8')
            temp_product_path = product_temp.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as review_temp:
            review_df.to_csv(review_temp.name, index=False, encoding='utf-8')
            temp_review_path = review_temp.name

        try:
            # Generate data insights (will upload to R2 internally)
            generate_insights_module.main(temp_product_path, temp_review_path, search_id)

            # Generate review analysis (will upload to R2 internally)
            review_analyzer.main(temp_product_path, temp_review_path, search_id)

            # Mark insights as generated in the database
            DBService.update_insight_generated(db, search_id, True)
            print(f"✓ Insights generated and marked in database for search_id: {search_id}")

        finally:
            # Clean up temporary files
            os.unlink(temp_product_path)
            os.unlink(temp_review_path)

        # Log execution time
        end_time = time.time()
        duration_seconds = end_time - start_time
        duration_minutes = duration_seconds / 60
        print(f"\n{'='*60}")
        print(f"Insights generation completed for search_id: {search_id}")
        print(f"Ended at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"Total execution time: {duration_minutes:.2f} minutes ({duration_seconds:.2f} seconds)")
        print(f"{'='*60}\n")

    except Exception as e:
        end_time = time.time()
        duration_seconds = end_time - start_time
        print(f"\n{'='*60}")
        print(f"Error during insights generation: {e}")
        print(f"Failed after: {duration_seconds:.2f} seconds ({duration_seconds/60:.2f} minutes)")
        print(f"{'='*60}\n")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@router.post("/generate_insights/{search_id}")
async def generate_insights_endpoint( search_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db),  current_user_id = Depends(get_current_user_id)):
    """
    API Endpoint to trigger insights generation for a given search ID. This endpoint will call the generate_insights function to process the scrapped data and generate insights.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to generate insights for this search"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="No output file found for this search")

    try:
        background_tasks.add_task( generate_insights, search_id=search_id, output_file_name=search_record.output_filename)
        return {
            "message": "Insights generation initiated successfully",
            "search_id": search_id,
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

#define API endpoints here to call the create_scrapping_task function when a request is made to start a new scrapping task.
@router.post("/initiate_scrapping", response_model= ScrapperResponse, status_code=status.HTTP_202_ACCEPTED)
async def scrape_products(
        request: ScrapperRequest,
        background_tasks: BackgroundTasks,  
        db: Session = Depends(get_db),
        current_user_id = Depends(get_current_user_id)
):
    """
    API endpoint to initiate the scrapping process for a given product and user ID.
    This endpoint will create a new search record in the database and start the scrapping process in the background.
    """

    #validate user_id
    user = DBService.getUserById(db, int(current_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        search = DBService.create_search(db, int(current_user_id), ",".join(request.platform), request.product_name, request.category, request.deep_details, request.max_products, request.include_reviews, request.auto_generate_insights)

        # Wrap scraping to run in thread (fixes Playwright asyncio loop conflict)
        async def run_scrapping_in_thread():
            """Run blocking scraper outside asyncio loop"""
            import asyncio
            await asyncio.to_thread(
                start_scrapping,
                search_id=search.search_id,
                platform=request.platform,
                product_name=request.product_name,
                category=request.category,
                deep_details=request.deep_details,
                max_products=request.max_products,
                include_reviews=request.include_reviews,
                auto_generate_insights=request.auto_generate_insights
            )

        background_tasks.add_task(run_scrapping_in_thread)

        return ScrapperResponse(
            status="success",
            message="Scrapping initiated successfully",
            search_id=search.search_id,
            data_path=None  # You can update this with the actual path to the stored data file once scrapping is completed
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/search/{search_id}", response_model=ScrapperStatus)
async def get_scrapping_status(search_id: str, db: Session = Depends(get_db), current_user_id = Depends(get_current_user_id)):
    " API Endpoint to get current status of the scrapping task for a given search ID. This endpoint will return the current status, progress, and other relevant details about the scrapping task."
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")
    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )

    try:
        return ScrapperStatus(
            search_id=search_record.search_id,
            user_id=str(search_record.user_id),
            platform=search_record.platforms.split(","),
            product_name=search_record.product_name,  # You can update this with the actual number of products scrapped so far
            status=search_record.status,
            deep_details=search_record.deep_details or 0,
            include_reviews=search_record.include_reviews or 0,
            max_products=search_record.max_products or 0,
            started_at=search_record.started_at,
            completed_at=search_record.completed_at,
            progress=25.0, # You can update this with the actual progress percentage of the scrapping task
            output_file_name=search_record.output_filename,
            total_products_scraped=search_record.total_products_scraped or 0,
            insight_generated=bool(search_record.insight_generated),
            data_quality_passed=bool(search_record.data_quality_passed)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search_detail/{search_id}", response_model=ScrappedData)
async def get_search_detail(search_id: str, db: Session = Depends(get_db), current_user_id = Depends(get_current_user_id)):
    " API Endpoint to get detailed information about a specific search record for a given search ID. This endpoint will return all relevant details about the search record, including the platforms being scraped, product name, category, deep details flag, max products, include reviews flag, and other relevant information."
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")
    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )
    try:
        return ScrappedData(
            search_id=search_record.search_id,
            product_name=search_record.product_name,
            user_id=str(search_record.user_id),
            deep_details=search_record.deep_details,
            include_reviews=search_record.include_reviews,
            platform=search_record.platforms.split(","),
            output_file_name=search_record.output_filename,
            status=search_record.status,
            completed_at=search_record.completed_at,
            total_products_scraped=0,
            insight_generated=bool(search_record.insight_generated),
            data_quality_passed=bool(search_record.data_quality_passed)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/my_searches")
async def get_user_searches(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get all search records for a given user ID with pagination metadata.
    Returns a dict with searches list, total count, limit, and offset.
    """
    user = DBService.getUserById(db, int(current_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        print(f"Fetching searches for user_id: {current_user_id} with limit: {limit} and offset: {offset}")

        # Get total count
        from backend.models.db_models import Search
        total_count = db.query(Search).filter(Search.user_id == int(current_user_id)).count()

        # Get paginated searches
        searches = DBService.get_searches_by_user_id(db, int(current_user_id), limit, offset)
        print(f"Found {len(searches)} searches for user_id: {current_user_id}, total: {total_count}")

        search_list = [
            ScrapperStatus(
                search_id=search.search_id,
                user_id=str(search.user_id),
                platform=search.platforms.split(",") if search.platforms else ["amazon"],
                product_name=search.product_name,
                status=search.status,
                deep_details=search.deep_details or 0,
                include_reviews=search.include_reviews or 0,
                max_products=search.max_products or 0,
                started_at=search.started_at,
                completed_at=search.completed_at,
                progress=25.0,  # You can update this with the actual progress percentage of the scrapping task
                total_products_scraped=search.total_products_scraped or 0,
                insight_generated=bool(search.insight_generated),
                data_quality_passed=bool(search.data_quality_passed)
            ) for search in searches
        ]

        return {
            "searches": search_list,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        print(f"Error in get_user_searches: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search_statistics", response_model=SearchStatistics)
async def get_search_statistics(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get aggregate statistics for all searches of the current user.
    Returns total, completed, in-progress, and failed search counts.
    """
    user = DBService.getUserById(db, int(current_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        print(f"Fetching search statistics for user_id: {current_user_id}")
        stats = DBService.get_user_search_statistics(db, int(current_user_id))
        return SearchStatistics(**stats)
    except Exception as e:
        print(f"Error in get_search_statistics: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/csv_preview/{search_id}")
async def get_csv_preview(
    search_id: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get CSV preview (top 10 rows) for a search.
    Returns column names and top 10 rows as JSON.
    Reads from R2 cloud storage.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="Output file not found for this search")

    try:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        print(f"Reading CSV preview from R2 for search_id: {search_id}")

        # Read CSV from R2
        df = storage.get_scraping_results(search_id, file_type='products')

        if df is None:
            raise HTTPException(status_code=404, detail=f"CSV file not found in R2 for search_id: {search_id}")

        # Get top 10 rows
        preview_df = df.head(10)

        # Replace NaN and infinity values with None for JSON compliance
        preview_df = preview_df.replace([np.inf, -np.inf], None)
        preview_df = preview_df.where(pd.notna(preview_df), None)

        # Convert to dict format and sanitize for JSON compliance
        rows = preview_df.to_dict(orient='records')
        rows = sanitize_csv_data(rows)

        # Return JSON response
        return {
            "columns": df.columns.tolist(),
            "rows": rows,
            "total_rows": len(df),
            "preview_rows": len(rows)
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading CSV file from R2: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading CSV file: {str(e)}")


@router.get("/download_csv/{search_id}")
async def download_csv(
    search_id: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to download the full CSV file for a search.
    Returns the CSV file as a downloadable attachment from R2.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download this file"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="Output file not found for this search")

    try:
        from backend.storage.r2_storage import get_storage
        import tempfile

        storage = get_storage()

        print(f"Downloading CSV from R2 for search_id: {search_id}")

        # Read CSV from R2
        df = storage.get_scraping_results(search_id, file_type='products')

        if df is None:
            raise HTTPException(status_code=404, detail="CSV file not found in R2")

        # Create temporary file for download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as temp_file:
            df.to_csv(temp_file.name, index=False, encoding='utf-8')
            temp_path = temp_file.name

        # Return file as download
        filename = search_record.output_filename
        if not filename.endswith('.csv'):
            filename = filename + '.csv'

        return FileResponse(
            path=temp_path,
            filename=filename,
            media_type='text/csv',
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error downloading CSV file: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error downloading CSV file: {str(e)}")


@router.get("/brand_insights/{search_id}")
async def get_brand_insights(
    search_id: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get brand insights for a search from R2.
    Returns brand ranking, ratings, trust scores, and sentiment analysis.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="Output file not found for this search")

    try:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        print(f"Reading brand insights from R2 for search_id: {search_id}")

        # Read brand insights from R2
        df = storage.get_brand_insights(search_id)

        if df is None:
            raise HTTPException(status_code=404, detail="Brand insights not found in R2. Please generate insights first.")

        # Replace NaN and infinity values with None for JSON compliance
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notna(df), None)

        # Convert to dict format and sanitize for JSON compliance
        brands = df.to_dict(orient='records')
        brands = sanitize_csv_data(brands)

        return {
            "total_brands": len(brands),
            "brands": brands
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading brand insights from R2: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading brand insights: {str(e)}")


@router.get("/review_analysis/{search_id}")
async def get_review_analysis(
    search_id: str,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get review analysis for a search from R2.
    Returns sentiment analysis, review summaries, and attribute ratings for each brand.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="Output file not found for this search")

    try:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        print(f"Reading review analysis from R2 for search_id: {search_id}")

        # Read review analysis from R2
        df = storage.get_review_analysis(search_id)

        if df is None:
            raise HTTPException(status_code=404, detail="Review analysis not found in R2. Please generate insights first.")

        print(f"Review analysis read successfully from R2 with {len(df)} records")

        # Replace NaN and infinity values with None for JSON compliance
        df = df.replace([np.inf, -np.inf], None)
        df = df.where(pd.notna(df), None)

        # Convert to dict format and sanitize for JSON compliance
        reviews = df.to_dict(orient='records')
        reviews = sanitize_csv_data(reviews)

        return {
            "total_brands": len(reviews),
            "reviews": reviews
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading review analysis from R2: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading review analysis: {str(e)}")


@router.get("/silver_data/{search_id}")
async def get_silver_data(
    search_id: str,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id)
):
    """
    API Endpoint to get processed silver data for a search from R2.
    Returns detailed product data with pagination.
    """
    search_record = DBService.get_search_by_id(db, search_id)
    if not search_record:
        raise HTTPException(status_code=404, detail="Search record not found")

    if search_record.user_id != int(current_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this search"
        )

    if not search_record.output_filename:
        raise HTTPException(status_code=404, detail="Output file not found for this search")

    try:
        from backend.storage.r2_storage import get_storage
        storage = get_storage()

        print(f"Reading silver data from R2 for search_id: {search_id}")

        # Read silver data from R2
        df = storage.get_silver_data(search_id)

        if df is None:
            raise HTTPException(
                status_code=404,
                detail="Silver data not found in R2. Please generate insights first."
            )

        # Apply pagination
        total_rows = len(df)
        print(f"Total rows in silver data: {total_rows}")
        paginated_df = df.iloc[offset:offset + limit]

        # Replace NaN and infinity values with None for JSON compliance
        paginated_df = paginated_df.replace([np.inf, -np.inf], None)
        paginated_df = paginated_df.where(pd.notna(paginated_df), None)

        # Convert to dict format and sanitize for JSON compliance
        products = paginated_df.to_dict(orient='records')
        products = sanitize_csv_data(products)

        return {
            "total_products": total_rows,
            "limit": limit,
            "offset": offset,
            "returned_count": len(products),
            "products": products
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error reading silver data from R2: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error reading silver data: {str(e)}")


# def create_scrapping_task(
#         user_id: int,
#         platform: list,
#         product_name: str,
#         category: str = None,
#         deep_details: bool = True,
#         max_products: int = 80,
#         include_reviews: bool = False
# ):
#     """
#     Create a scrapping task in the database and start the scrapping process in the background.
#     """
#     from backend.services.db_services import DBService
#     db = SessionLocal()
#     try:
#         # Create a new search record in the database
#         platforms_str = ",".join(platform)
#         search_record = DBService.create_search(db, user_id, platforms_str, product_name, category, deep_details, max_products, include_reviews)
        
#         # Start the scrapping process in the background
#         from fastapi import BackgroundTasks
#         background_tasks = BackgroundTasks()
#         background_tasks.add_task(start_scrapping, search_id=search_record.search_id, platform=platform, product_name=product_name, category=category, deep_details=deep_details, max_products=max_products, include_reviews=include_reviews)
        
#         return search_record
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         db.close()