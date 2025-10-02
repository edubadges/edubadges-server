# Use the official uv image with Python 3.9
FROM ghcr.io/astral-sh/uv:python3.9-bookworm

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

COPY ./docker/entrypoint-dev.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Install any needed packages specified in requirements.txt
RUN uv pip install --system --no-cache -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the specified command within the container
CMD ["sh", "/entrypoint.sh"]
