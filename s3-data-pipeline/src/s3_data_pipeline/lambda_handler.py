from s3_data_pipeline.logging_conf import configure_logging
from s3_data_pipeline.pipeline import run

configure_logging()


def lambda_handler(event, context):
    return run()
