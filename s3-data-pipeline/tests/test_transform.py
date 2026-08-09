import polars as pl

from s3_data_pipeline.transform import clean_weather, summarize_by_station

# Matches the schema extract.py forces at scan time: numeric measurement
# columns arrive as (whitespace-padded) strings, parsed later in transform.py.
RAW_COLUMNS = [
    "STATION",
    "DATE",
    "NAME",
    "LATITUDE",
    "LONGITUDE",
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
]
_STRING_COLUMNS = {
    "STATION",
    "DATE",
    "NAME",
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
}


def _raw_frame(rows: list[dict]) -> pl.LazyFrame:
    schema = {c: pl.Utf8 if c in _STRING_COLUMNS else pl.Float64 for c in RAW_COLUMNS}
    return pl.DataFrame(rows, schema=schema).lazy()


def test_clean_weather_replaces_sentinel_missing_values_with_null():
    raw = _raw_frame(
        [
            {
                "STATION": "001",
                "DATE": "2024-01-01",
                "NAME": "TEST STATION",
                "LATITUDE": 10.0,
                "LONGITUDE": 20.0,
                "TEMP": "9999.9",  # sentinel for missing
                "DEWP": " 30.0",
                "MAX": "9999.9",
                "MIN": " 20.0",
                "WDSP": "999.9",  # sentinel for missing
                "MXSPD": " 10.0",
                "GUST": " 15.0",
                "VISIB": " 10.0",
                "PRCP": "99.99",  # sentinel for missing
                "SNDP": "999.9",
            }
        ]
    )

    result = clean_weather(raw).collect()

    # TEMP was the sentinel value, so the row is dropped entirely by the
    # "no usable temperature reading" filter.
    assert result.height == 0


def test_clean_weather_derives_celsius_and_normalizes_sentinels():
    raw = _raw_frame(
        [
            {
                "STATION": "001",
                "DATE": "2024-01-01",
                "NAME": "TEST STATION",
                "LATITUDE": 10.0,
                "LONGITUDE": 20.0,
                "TEMP": "  32.0",  # 0 C, with padding like real GSOD rows
                "DEWP": " 30.0",
                "MAX": " 40.0",
                "MIN": " 20.0",
                "WDSP": "999.9",  # sentinel -> should become null
                "MXSPD": " 10.0",
                "GUST": " 15.0",
                "VISIB": " 10.0",
                "PRCP": " 0.50",
                "SNDP": "999.9",
            }
        ]
    )

    result = clean_weather(raw).collect()

    assert result.height == 1
    row = result.row(0, named=True)
    assert row["temp_c"] == 0.0
    assert row["wind_speed_kt"] is None
    assert row["station_id"] == "001"


def test_summarize_by_station_aggregates_per_station():
    detail = pl.DataFrame(
        {
            "station_id": ["001", "001", "002"],
            "station_name": ["A", "A", "B"],
            "temp_f": [50.0, 60.0, 70.0],
            "wind_speed_kt": [5.0, 15.0, 10.0],
            "precip_in": [0.1, 0.2, 0.0],
        }
    ).lazy()

    summary = summarize_by_station(detail).collect().sort("station_id")

    assert summary.height == 2
    station_001 = summary.filter(pl.col("station_id") == "001").row(0, named=True)
    assert station_001["days_observed"] == 2
    assert station_001["avg_temp_f"] == 55.0
    assert station_001["min_temp_f"] == 50.0
    assert station_001["max_temp_f"] == 60.0
    assert station_001["total_precip_in"] == 0.3
