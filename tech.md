# Technology Stack

## Core Framework
- **Django 4.2.24**: Python web framework
- **Python 3.9**: Primary programming language
- **Django REST Framework 3.15.2**: API development
- **MySQL**: Primary database (mysqlclient 2.2.4)
- **Memcached**: Caching layer

## Key Libraries & Dependencies
- **Pillow 10.3.0**: Image processing for badge graphics
- **CairoSVG 2.7.0**: SVG to PNG conversion for badge rendering
- **Celery 5.2.7**: Asynchronous task processing
- **GraphQL**: API queries via graphene-django 3.2.2
- **OAuth2**: Authentication via django-oauth-toolkit 2.2.0
- **LTI 1.3**: Learning management system integration
- **Open Badges**: Badge validation and standards compliance

## Authentication & Authorization
- **Django Allauth**: Social authentication
- **Social Auth**: Multiple provider support (eduID, SURFConext)
- **Django OTP**: Two-factor authentication
- **Rules**: Permission framework

## Development Tools
- **Ruff**: Code linting and formatting (120 char line length, single quotes)
- **Docker**: Containerized development environment
- **pytest**: Testing framework

## Common Commands

### Local Development Setup
```bash
# Environment setup
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Database setup
./manage.py migrate
./manage.py seed -c  # Seed with test data

# Run development server
source env_vars.sh
./manage.py runserver
```

### Docker Development
```bash
# Set environment variables in .env.docker
docker compose up  # Start all services
docker compose up -d  # Run in background
```

### Common Management Commands
```bash
./manage.py test  # Run tests
./manage.py show_urls  # List all URL patterns
./manage.py addstatictoken superuser  # Generate TOTP for admin
```

### Database Operations
```bash
./manage.py migrate  # Apply migrations
./manage.py seed  # Add seed data
./manage.py seed -c  # Truncate and reseed
```

## Environment Configuration
- Copy `env_vars.sh.example` to `env_vars.sh` and configure
- Required: Database credentials, email settings, OAuth secrets
- Staff dashboard: `/staff/superlogin` (superuser/secret with seeds)
- API docs: `/api/schema/swagger-ui/`
