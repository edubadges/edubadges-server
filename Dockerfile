# Use the official Python image from the Docker Hub
FROM python:3.9

ARG GUNICORN_WORKERS=3
ARG GUNICORN_THREADS=1

# Install system dependencies for cairo and MySQL client
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# Make the locale en_US.UTF-8 available which is needed for mysql client
RUN apt-get update && apt-get install -y locales \
    && locale-gen en_US.UTF-8 && dpkg-reconfigure locales \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /env/bin/pip install gunicorn

ENV VIRTUAL_ENV /env
ENV PATH /env/bin:$PATH

# Make port 8000 available to the world outside this container
EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--log-level", "debug", "--workers", "3", "--pythonpath", "/app/apps", "wsgi:application"]
