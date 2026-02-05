# Use the official Python image from the Docker Hub
FROM python:3.9

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

# Set execute permissions on entrypoint script
RUN chmod +x /app/docker/entrypoint.sh

RUN pip install --upgrade pip setuptools wheel
# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the specified command within the container
CMD ["sh", "/app/docker/entrypoint.sh"]
