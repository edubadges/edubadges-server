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

RUN set -ex \
    && python -m venv /env \
    && /env/bin/pip install --upgrade pip \
    && /env/bin/pip install --no-cache-dir -r /app/requirements.txt \
    && /env/bin/pip install gunicorn

COPY docker/entrypoint-k8s.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV VIRTUAL_ENV=/env
ENV PATH=/env/bin:$PATH

# Set required environment variables for being able to run collectstatic during build
ENV DOMAIN=build.example.com \
    UI_URL=http://build.example.com \
    DEFAULT_DOMAIN=http://build.example.com \
    ACCOUNT_SALT=buildsalt \
    EDUID_PROVIDER_URL=http://build.example.com \
    ROOT_INFO_SECRET_KEY=buildsecret \
    UNSUBSCRIBE_SECRET_KEY=buildunsubscribe \
    TIME_STAMPED_OPEN_BADGES_BASE_URL=http://build.example.com \
    BADGR_DB_NAME=builddb \
    BADGR_DB_USER=builduser \
    BADGR_DB_PASSWORD=buildpass \
    EMAIL_HOST=build.example.com \
    DEFAULT_FROM_EMAIL=build@example.com \
    EDU_ID_SECRET=buildsecret \
    OIDC_RS_SECRET=buildsecret

# Run collectstatic with build-specific settings
RUN DJANGO_SETTINGS_MODULE=apps.mainsite.settings_build /env/bin/python3 -m django collectstatic --noinput

# Make port 8000 available to the world outside this container
EXPOSE 8000

ENTRYPOINT ["sh", "/entrypoint.sh"]

CMD ["gunicorn", "--bind", ":8000", "--log-level", "debug", "--workers", "3", "--pythonpath", "/app/apps", "wsgi:application"]
