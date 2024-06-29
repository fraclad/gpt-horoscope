# Use the official AWS Lambda Python 3.10 image
FROM public.ecr.aws/lambda/python:3.10

# Set the OpenAI API key as a build argument and environment variable
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}

# Install build dependencies
RUN yum -y update && yum -y install \
    gcc \
    gcc-c++ 

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install openai kerykeion

# Copy necessary files to the working directory
COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY prompt.txt ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (filename.function_name)
CMD ["lambda_function.lambda_handler"]
