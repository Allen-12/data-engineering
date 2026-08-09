"""Load: write transformed output to the user's own destination S3 bucket.

Unlike extract (anonymous read of a public bucket), this uses the caller's
real AWS credentials — resolved the standard way (env vars, `~/.aws`
profile, or instance role) — since writing requires an authenticated,
authorized identity.
"""

from __future__ import annotations

import datetime as dt

import polars as pl

from s3_data_pipeline.config import Settings
from s3_data_pipeline.logging_conf import get_logger

logger = get_logger(__name__)


def write_output(
    detail: pl.DataFrame, summary: pl.DataFrame, settings: Settings
) -> dict[str, str]:
    """Write the detail and summary tables as Parquet, partitioned by run date."""
    run_date = dt.datetime.now(tz=dt.UTC).date().isoformat()
    storage_options = {"aws_region": settings.aws_region}

    detail_path = f"s3://{settings.dest_bucket}/{settings.dest_prefix}/detail/run_date={run_date}/weather_detail.parquet"
    summary_path = f"s3://{settings.dest_bucket}/{settings.dest_prefix}/summary/run_date={run_date}/weather_summary.parquet"

    logger.info("Writing %d detail rows to %s", detail.height, detail_path)
    detail.write_parquet(detail_path, storage_options=storage_options)

    logger.info("Writing %d summary rows to %s", summary.height, summary_path)
    summary.write_parquet(summary_path, storage_options=storage_options)

    return {"detail": detail_path, "summary": summary_path}
