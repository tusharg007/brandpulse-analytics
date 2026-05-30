"""Unit tests for ETL transform logic."""
import pandas as pd
from datetime import datetime


def test_transform_outlier_flagging():
    """Records with return_rate > 0.3 should be flagged as anomalous."""
    # Import inside test to avoid app context issues
    from app.services.etl_service import transform_data

    df = pd.DataFrame([
        {'brand_id': 1, 'date': '2024-01-15', 'revenue': 10000, 'units_sold': 50,
         'platform': 'Amazon', 'return_rate': 0.05},
        {'brand_id': 1, 'date': '2024-01-16', 'revenue': 20000, 'units_sold': 100,
         'platform': 'Flipkart', 'return_rate': 0.40},
    ])

    result = transform_data(df)

    # Find the row with high return rate
    anomalous = result[result['return_rate'] > 0.3]
    normal = result[result['return_rate'] <= 0.3]

    assert len(anomalous) == 1
    assert anomalous.iloc[0]['is_anomalous'] == True
    assert len(normal) == 1
    assert normal.iloc[0]['is_anomalous'] == False


def test_transform_revenue_per_unit():
    """revenue_per_unit should be calculated correctly."""
    from app.services.etl_service import transform_data

    df = pd.DataFrame([
        {'brand_id': 1, 'date': '2024-03-01', 'revenue': 5000, 'units_sold': 10,
         'platform': 'Direct', 'return_rate': 0.1},
    ])

    result = transform_data(df)
    assert result.iloc[0]['revenue_per_unit'] == 500.0


def test_transform_deduplication():
    """Duplicate (brand_id, date, platform) records should be aggregated."""
    from app.services.etl_service import transform_data

    df = pd.DataFrame([
        {'brand_id': 1, 'date': '2024-02-01', 'revenue': 3000, 'units_sold': 30,
         'platform': 'Amazon', 'return_rate': 0.1},
        {'brand_id': 1, 'date': '2024-02-01', 'revenue': 7000, 'units_sold': 70,
         'platform': 'Amazon', 'return_rate': 0.2},
    ])

    result = transform_data(df)

    # Should be deduplicated to 1 row
    assert len(result) == 1
    assert result.iloc[0]['revenue'] == 10000  # sum
    assert result.iloc[0]['units_sold'] == 100  # sum


def test_transform_invalid_dates():
    """Rows with invalid dates should be dropped."""
    from app.services.etl_service import transform_data

    df = pd.DataFrame([
        {'brand_id': 1, 'date': '2024-01-15', 'revenue': 5000, 'units_sold': 10,
         'platform': 'Amazon', 'return_rate': 0.05},
        {'brand_id': 2, 'date': 'not-a-date', 'revenue': 3000, 'units_sold': 5,
         'platform': 'Flipkart', 'return_rate': 0.1},
    ])

    result = transform_data(df)
    assert len(result) == 1


def test_transform_adds_ingestion_timestamp():
    """Transformed data should have an ingestion_timestamp column."""
    from app.services.etl_service import transform_data

    df = pd.DataFrame([
        {'brand_id': 1, 'date': '2024-05-01', 'revenue': 2000, 'units_sold': 20,
         'platform': 'Direct', 'return_rate': 0.08},
    ])

    result = transform_data(df)
    assert 'ingestion_timestamp' in result.columns
    assert result.iloc[0]['ingestion_timestamp'] is not None
