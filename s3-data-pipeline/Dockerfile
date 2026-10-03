FROM public.ecr.aws/lambda/python:3.12

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

CMD ["s3_data_pipeline.lambda_handler.lambda_handler"]
