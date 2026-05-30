"""
ETL Pipeline Service for BrandPulse.

Pipeline steps:
  1. Extract  — Read CSV files from /data/raw/
  2. Transform — Pandas cleaning, outlier flagging, deduplication
  3. Load    — Bulk upsert into PostgreSQL sales_records table
  4. Log     — Write ETLLog entry with count and status

──────────────────────────────────────────────────────────────
PRODUCTION NOTE — Azure Blob Storage Integration
──────────────────────────────────────────────────────────────
In production, step 1 (Extract) would pull from Azure Blob Storage
instead of reading local CSV files. The implementation would be:

    from azure.storage.blob import BlobServiceClient

    connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service.get_container_client('sales-data')

    for blob in container_client.list_blobs(name_starts_with='raw/'):
        blob_client = container_client.get_blob_client(blob)
        stream = blob_client.download_blob()
        df = pd.read_csv(io.BytesIO(stream.readall()))
        # ... continue with transform step

This maps directly to Azure Data Factory pipelines where:
  - ADF Copy Activity → extracts from Blob Storage
  - ADF Data Flow → applies transformations
  - ADF Sink → loads into Azure SQL / PostgreSQL
──────────────────────────────────────────────────────────────
"""
import os
import glob
from datetime import datetime

import pandas as pd
from sqlalchemy import text
from app.extensions import db
from app.models import SalesRecord, ETLLog
from app.services.cache_service import invalidate_cache


def run_etl_pipeline() -> dict:
    """Execute the full ETL pipeline. Returns summary dict."""
    log_entry = ETLLog(
        run_timestamp=datetime.utcnow(),
        status='running',
    )
    db.session.add(log_entry)
    db.session.commit()

    try:
        # ── 1. EXTRACT ──────────────────────────────────
        raw_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'raw')
        csv_files = glob.glob(os.path.join(raw_dir, '*.csv'))

        if not csv_files:
            log_entry.status = 'success'
            log_entry.records_processed = 0
            log_entry.error_message = 'No CSV files found in /data/raw/'
            db.session.commit()
            return {'records_processed': 0, 'status': 'success'}

        frames = []
        for csv_path in csv_files:
            df = pd.read_csv(csv_path)
            frames.append(df)

        df = pd.concat(frames, ignore_index=True)

        # ── 2. TRANSFORM ────────────────────────────────
        df = transform_data(df)

        # ── 3. LOAD ─────────────────────────────────────
        records_loaded = load_data(df)

        # ── 4. LOG ──────────────────────────────────────
        log_entry.records_processed = records_loaded
        log_entry.status = 'success'
        db.session.commit()

        # Invalidate analytics cache so dashboards pick up new data
        invalidate_cache('analytics:*')

        return {'records_processed': records_loaded, 'status': 'success'}

    except Exception as e:
        log_entry.status = 'failed'
        log_entry.error_message = str(e)
        db.session.commit()
        raise


def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply transformations to raw sales data:
      - Parse and validate dates
      - Calculate revenue_per_unit
      - Flag outliers (return_rate > 0.3)
      - Aggregate duplicates by (brand_id, date, platform)
      - Add ingestion_timestamp
    """
    # Parse dates
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['date'] = df['date'].dt.date

    # Ensure numeric columns
    df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
    df['units_sold'] = pd.to_numeric(df['units_sold'], errors='coerce').fillna(0).astype(int)
    df['return_rate'] = pd.to_numeric(df['return_rate'], errors='coerce').fillna(0)

    # Calculate revenue per unit
    df['revenue_per_unit'] = df.apply(
        lambda row: round(row['revenue'] / row['units_sold'], 2)
        if row['units_sold'] > 0 else 0,
        axis=1
    )

    # Flag outliers: return_rate > 30%
    df['is_anomalous'] = df['return_rate'] > 0.3

    # Aggregate duplicates by (brand_id, date, platform)
    agg_df = df.groupby(['brand_id', 'date', 'platform'], as_index=False).agg({
        'revenue': 'sum',
        'units_sold': 'sum',
        'return_rate': 'mean',
        'revenue_per_unit': 'mean',
        'is_anomalous': 'max',
    })

    # Add ingestion timestamp
    agg_df['ingestion_timestamp'] = datetime.utcnow()

    return agg_df


def load_data(df: pd.DataFrame) -> int:
    """Bulk upsert records into the sales_records table. Returns count loaded."""
    loaded = 0

    for _, row in df.iterrows():
        existing = SalesRecord.query.filter_by(
            brand_id=int(row['brand_id']),
            date=row['date'],
            platform=row['platform'],
        ).first()

        if existing:
            existing.revenue = float(row['revenue'])
            existing.units_sold = int(row['units_sold'])
            existing.return_rate = float(row['return_rate'])
            existing.revenue_per_unit = float(row['revenue_per_unit'])
            existing.is_anomalous = bool(row['is_anomalous'])
            existing.ingestion_timestamp = row['ingestion_timestamp']
        else:
            record = SalesRecord(
                brand_id=int(row['brand_id']),
                date=row['date'],
                revenue=float(row['revenue']),
                units_sold=int(row['units_sold']),
                platform=row['platform'],
                return_rate=float(row['return_rate']),
                revenue_per_unit=float(row['revenue_per_unit']),
                is_anomalous=bool(row['is_anomalous']),
                ingestion_timestamp=row['ingestion_timestamp'],
            )
            db.session.add(record)

        loaded += 1

    db.session.commit()
    return loaded
