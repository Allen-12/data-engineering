"""Pipeline entrypoint: extract -> transform -> load.

Run with:
    uv run python -m s3_data_pipeline.pipeline
"""

from __future__ import annotations

from s3_data_pipeline.config import get_settings
from s3_data_pipeline.extract import read_source
from s3_data_pipeline.load import write_output
from s3_data_pipeline.logging_conf import configure_logging, get_logger
from s3_data_pipeline.transform import clean_weather, summarize_by_station

logger = get_logger(__name__)


def run() -> dict[str, str]:
    settings = get_settings()
    logger.info(
        "Starting pipeline: source=s3://%s/%d (sample=%d) -> dest=s3://%s/%s",
        settings.source_bucket,
        settings.source_year,
        settings.sample_size,
        settings.dest_bucket,
        settings.dest_prefix,
    )

    raw = read_source(settings)
    detail = clean_weather(raw).collect()
    summary = summarize_by_station(detail.lazy()).collect()

    logger.info(
        "Transformed %d detail rows into %d station summaries",
        detail.height,
        summary.height,
    )

    output_paths = write_output(detail, summary, settings)
    logger.info("Pipeline complete. Wrote: %s", output_paths)
    return output_paths


def main() -> None:
    configure_logging()
    run()


if __name__ == "__main__":
    main()
