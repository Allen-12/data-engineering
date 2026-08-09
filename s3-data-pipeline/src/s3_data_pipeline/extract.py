"""Extract: discover and lazily read the public NOAA GSOD dataset from S3.

Dataset: NOAA Global Surface Summary of the Day (GSOD), part of the AWS
Open Data Registry — one CSV per weather station per year, publicly
readable with no AWS credentials required.
https://registry.opendata.aws/noaa-gsod/
"""

from __future__ import annotations

import boto3
import polars as pl
from botocore import UNSIGNED
from botocore.config import Config

from s3_data_pipeline.config import Settings
from s3_data_pipeline.logging_conf import get_logger

logger = get_logger(__name__)

# Force these to a single consistent dtype at scan time. Two reasons:
# station IDs carry leading zeros that get silently dropped if inferred as
# an integer, and the "numeric" measurement columns are inconsistently
# inferred as String vs Float64 across different station files (their
# quoted values carry padding whitespace), which breaks a multi-file scan
# that expects one schema. We read them as strings here and do the real
# numeric parsing explicitly in transform.py.
_SCHEMA_OVERRIDES = {
    "STATION": pl.Utf8,
    "TEMP": pl.Utf8,
    "DEWP": pl.Utf8,
    "MAX": pl.Utf8,
    "MIN": pl.Utf8,
    "WDSP": pl.Utf8,
    "MXSPD": pl.Utf8,
    "GUST": pl.Utf8,
    "VISIB": pl.Utf8,
    "PRCP": pl.Utf8,
    "SNDP": pl.Utf8,
}


def list_station_files(settings: Settings) -> list[str]:
    """Return up to `sample_size` s3:// paths for the configured source year.

    Uses an unsigned (anonymous) boto3 client since the source bucket is
    public and listing it doesn't require the user's own AWS credentials.
    """
    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=Config(signature_version=UNSIGNED),
    )
    prefix = f"{settings.source_year}/"
    response = s3.list_objects_v2(
        Bucket=settings.source_bucket,
        Prefix=prefix,
        MaxKeys=settings.sample_size,
    )
    keys = [obj["Key"] for obj in response.get("Contents", [])]
    if not keys:
        raise RuntimeError(
            f"No objects found under s3://{settings.source_bucket}/{prefix}"
        )
    logger.info(
        "Discovered %d source files under s3://%s/%s",
        len(keys),
        settings.source_bucket,
        prefix,
    )
    return [f"s3://{settings.source_bucket}/{key}" for key in keys]


def read_source(settings: Settings) -> pl.LazyFrame:
    """Lazily scan the discovered station CSVs directly from S3."""
    paths = list_station_files(settings)
    return pl.scan_csv(
        paths,
        schema_overrides=_SCHEMA_OVERRIDES,
        storage_options={"aws_region": settings.aws_region, "skip_signature": "true"},
    )
