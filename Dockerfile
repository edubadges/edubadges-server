# Use the official uv Docker image with Python 3.9 as base
FROM ghcr.io/astral-sh/uv:python3.9-trixie-slim as builder

# Install system dependencies for cairo and MySQL client
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    locales \
    git \
    default-libmysqlclient-dev \
    gcc \
    python3-dev \
    && locale-gen en_US.UTF-8 && dpkg-reconfigure locales \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy only requirements files first for better caching
COPY uv.lock pyproject.toml ./

# Install dependencies using uv sync (--system for Docker system installation)
RUN uv pip sync uv.lock --system

# Final stage - use the same Python+uv image for consistency
FROM ghcr.io/astral-sh/uv:python3.9-trixie-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libcairo2 \
    locales \
    git \
    && locale-gen en_US.UTF-8 && dpkg-reconfigure locales \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the rest of the application
COPY . /app

# Set execute permissions on entrypoint script
RUN chmod +x /app/docker/entrypoint.sh

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the specified command within the container
CMD ["sh", "/app/docker/entrypoint.sh"]
