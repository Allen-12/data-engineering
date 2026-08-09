"""Environment-driven configuration for the pipeline.

Loaded from a `.env` file (see `.env.example`) or real environment variables.
Only DEST_BUCKET is required — everything else has a sane default so the
pipeline can be run against the public source dataset with zero setup.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Source: NOAA Global Surface Summary of the Day (GSOD), a public AWS
    # Open Data dataset. One CSV per weather station per year, no
    # credentials required to read it.
    source_bucket: str = "noaa-gsod-pds"
    source_year: int = 2024
    # Number of station files to pull for this demo run, so a local run
    # finishes in seconds instead of scanning all ~12k stations for the year.
    sample_size: int = 50

    # Destination: the user's own bucket, written to under `processed/`.
    dest_bucket: str
    dest_prefix: str = "processed/noaa-gsod"

    aws_region: str = "us-east-1"


def get_settings() -> Settings:
    return Settings()
