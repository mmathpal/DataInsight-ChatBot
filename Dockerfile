# Use AWS Lambda Python 3.12 base image
FROM public.ecr.aws/lambda/python:3.12

# Upgrade pip
RUN pip3 install --upgrade pip

# Install Python dependencies
RUN pip3 install --platform manylinux2014_x86_64 \
    --target /var/task \
    --implementation cp --python-version 3.12 --only-binary=:all: \
    faiss-cpu==1.9.0 numpy boto3 requests requests-aws4auth python-dotenv

# Copy your Lambda function code
COPY lambda_function.py /var/task

# Set the CMD to your handler
CMD ["lambda_function.lambda_handler"]