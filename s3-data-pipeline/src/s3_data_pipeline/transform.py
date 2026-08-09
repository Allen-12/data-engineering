"""Transform: pure Polars functions turning raw GSOD rows into clean output.

Kept dependency-free (no S3/boto3 imports) so these are trivially unit
testable against small in-memory frames.

Two data-quality quirks handled here:
- The "numeric" columns arrive as whitespace-padded strings (`extract.py`
  forces them to Utf8 at scan time to keep a consistent schema across
  station files), so we parse them explicitly rather than trusting
  per-file type inference.
- NOAA encodes "missing" with sentinel values instead of nulls, one per
  column family (see the GSOD readme). We normalize those to real nulls,
  otherwise they'd quietly poison averages.
"""

from __future__ import annotations

import polars as pl

_NUMERIC_COLUMNS = (
    "TEMP",
    "DEWP",
    "MAX",
    "MIN",
    "WDSP",
    "MXSPD",
    "GUST",
    "VISIB",
    "PRCP",
    "SNDP",
)
_MISSING_9999_9 = ("TEMP", "DEWP", "MAX", "MIN")
_MISSING_999_9 = ("WDSP", "MXSPD", "GUST", "VISIB", "SNDP")
_MISSING_99_99 = ("PRCP",)


def _parse_numeric_strings(df: pl.LazyFrame) -> pl.LazyFrame:
    exprs = [
        pl.col(col).str.strip_chars().cast(pl.Float64, strict=False).alias(col)
        for col in _NUMERIC_COLUMNS
    ]
    return df.with_columns(exprs)


def _null_out_sentinels(df: pl.LazyFrame) -> pl.LazyFrame:
    exprs = []
    for col in _MISSING_9999_9:
        exprs.append(
            pl.when(pl.col(col) >= 9999.0).then(None).otherwise(pl.col(col)).alias(col)
        )
    for col in _MISSING_999_9:
        exprs.append(
            pl.when(pl.col(col) >= 999.0).then(None).otherwise(pl.col(col)).alias(col)
        )
    for col in _MISSING_99_99:
        exprs.append(
            pl.when(pl.col(col) >= 99.0).then(None).otherwise(pl.col(col)).alias(col)
        )
    return df.with_columns(exprs)


def clean_weather(df: pl.LazyFrame) -> pl.LazyFrame:
    """Clean, cast, and reshape raw GSOD rows into a tidy detail table.

    - Parses the padded numeric strings into real floats
    - Normalizes NOAA's sentinel "missing" values to nulls
    - Parses DATE into a real date type
    - Renames columns to clear, lowercase names
    - Derives temp_c from the Fahrenheit reading
    - Drops rows with no usable temperature reading
    """
    df = _parse_numeric_strings(df)
    df = _null_out_sentinels(df)
    return (
        df.with_columns(pl.col("DATE").str.to_date("%Y-%m-%d"))
        .select(
            pl.col("STATION").alias("station_id"),
            pl.col("DATE").alias("date"),
            pl.col("NAME").alias("station_name"),
            pl.col("LATITUDE").alias("latitude"),
            pl.col("LONGITUDE").alias("longitude"),
            pl.col("TEMP").alias("temp_f"),
            pl.col("DEWP").alias("dewp_f"),
            pl.col("MAX").alias("max_temp_f"),
            pl.col("MIN").alias("min_temp_f"),
            pl.col("WDSP").alias("wind_speed_kt"),
            pl.col("PRCP").alias("precip_in"),
        )
        .with_columns(((pl.col("temp_f") - 32) * 5 / 9).round(1).alias("temp_c"))
        .filter(pl.col("temp_f").is_not_null())
    )


def summarize_by_station(df: pl.LazyFrame) -> pl.LazyFrame:
    """Aggregate the cleaned detail table into one row per station."""
    return (
        df.group_by("station_id", "station_name")
        .agg(
            pl.len().alias("days_observed"),
            pl.col("temp_f").mean().round(1).alias("avg_temp_f"),
            pl.col("temp_f").min().alias("min_temp_f"),
            pl.col("temp_f").max().alias("max_temp_f"),
            pl.col("wind_speed_kt").mean().round(1).alias("avg_wind_speed_kt"),
            pl.col("precip_in").sum().round(2).alias("total_precip_in"),
        )
        .sort("avg_temp_f", descending=True)
    )
