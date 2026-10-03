# s3-data-pipeline

A small ETL pipeline: read a public dataset from S3, transform it with
[Polars](https://pola.rs), write the result back to S3 — built as a
portfolio project to demonstrate data engineering fundamentals in Python.

## What it does

```
┌─────────────────────────┐        ┌──────────────┐        ┌───────────────────────────┐
│ s3://noaa-gsod-pds/      │  scan  │              │  write │ s3://<your-bucket>/       │
│ <year>/<station>.csv     │ ─────► │   Polars     │ ─────► │ processed/noaa-gsod/      │
│ (public, anonymous read) │        │ transform    │        │ detail/  &  summary/      │
└─────────────────────────┘        └──────────────┘        └───────────────────────────┘
```

**Source**: [NOAA Global Surface Summary of the Day (GSOD)](https://registry.opendata.aws/noaa-gsod/)
— one CSV per weather station per year, public and free to read, no AWS
account needed for this half of the pipeline.

**Transform** (`src/s3_data_pipeline/transform.py`, pure Polars, unit tested):
- Normalizes NOAA's sentinel "missing" values (e.g. `9999.9`) to real nulls
- Parses dates, renames/casts columns, derives °C from the raw °F reading
- Drops rows with no usable temperature reading
- Aggregates a per-station summary (avg/min/max temp, avg wind speed, total precipitation, days observed)

**Load**: writes both a cleaned detail table and the per-station summary as
Parquet, partitioned by run date, into your own S3 bucket.

## Project structure

```
src/s3_data_pipeline/
  config.py         # env-driven settings (pydantic-settings)
  extract.py         # anonymous S3 discovery + scan of the public dataset
  transform.py         # pure Polars transform functions (unit tested)
  load.py                # authenticated write to your destination bucket
  pipeline.py              # orchestrates extract -> transform -> load
  logging_conf.py           # logging setup
  lambda_handler.py          # AWS Lambda entrypoint wrapping pipeline.run()
tests/
  test_transform.py          # unit tests, no AWS access required
Dockerfile                    # Lambda container image
infra/                         # Terraform: ECR, Lambda, IAM, logs, EventBridge schedule
```

## Running it

Requires [uv](https://docs.astral.sh/uv/) and an AWS account for the
destination bucket — see [SETUP.md](SETUP.md) for the one-time AWS setup
(IAM user, bucket, local credentials).

```bash
uv sync
cp .env.example .env   # then set DEST_BUCKET
uv run pytest          # unit tests, no AWS needed
uv run ruff check .    # lint
uv run python -m s3_data_pipeline.pipeline   # full run against real S3
```

Verify the output landed:

```bash
aws s3 ls s3://<your-bucket>/processed/noaa-gsod/ --recursive
```

## Tech stack & why

| Choice | Why |
|---|---|
| **Polars** | Fast, lazy, columnar — reads/writes S3 Parquet/CSV natively without a separate filesystem library |
| **boto3 (unsigned)** | Anonymous discovery of files in the public source bucket, no credentials needed to read |
| **pydantic-settings** | Typed, env-driven config instead of hardcoded buckets/paths |
| **uv** | Fast, modern Python dependency & environment management |
| **pytest** | Transform logic is pure functions over Polars frames — testable with zero AWS calls |

## Deploying to AWS (dev)

The pipeline also runs as an AWS Lambda function, defined entirely in
Terraform under `infra/`:

```
EventBridge schedule ──► Lambda (container image, arm64) ──► s3://<your-bucket>/processed/...
                              ▲                  │
                    ECR repo (image)       CloudWatch Logs (14-day retention)
```

- **Lambda as a container image**, not a zip — Polars' compiled binaries
  exceed Lambda's 250MB zip limit. Terraform builds the image with the
  `kreuzwerker/docker` provider and pushes it to ECR as part of `apply`.
- **Least-privilege execution role**: `s3:ListBucket`, `s3:GetObject` and
  `s3:PutObject` on the destination bucket only, plus writes to its own log group.
- **Two identities by design**: the narrow pipeline user runs the app; a
  separate `terraform-deployer` profile (broader permissions) provisions infra.
  The destination bucket is referenced, not managed, by Terraform.
- **Schedule is off by default** (`schedule_enabled = false`); flip it in
  `terraform.tfvars` and re-apply to enable the daily 06:00 UTC run.
- **Lambda gotchas handled**: `AWS_REGION` is reserved so it isn't set, and
  `POLARS_TEMP_DIR=/tmp/polars` is required because Lambda has no `$HOME`.

Requires Terraform and Docker running locally.

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # set dest_bucket_name
terraform init
terraform plan
terraform apply
aws lambda invoke --function-name s3-data-pipeline-dev --profile terraform-deployer out.json
```

## Roadmap

Planned next: CI/CD with GitHub Actions (OIDC instead of static keys), a
remote Terraform state backend, and failure alerting.
