# Project Structure

## Django App Organization

The project follows Django's app-based architecture with all apps located in the `apps/` directory:

### Core Apps
- **`mainsite/`**: Main Django project settings, URLs, middleware, and core utilities
- **`badgeuser/`**: User management, authentication, and user profiles
- **`issuer/`**: Badge creation, issuer management, and badge class definitions
- **`backpack/`**: Badge collection and sharing functionality for earners
- **`institution/`**: Educational institution management and hierarchies

### Feature Apps
- **`directaward/`**: Direct badge awarding system and bulk operations
- **`endorsement/`**: Badge endorsement and approval workflows  
- **`lti13/`**: LTI 1.3 integration for learning management systems
- **`lti_edu/`**: Educational LTI-specific functionality
- **`signing/`**: Digital signature and timestamping for badges
- **`notifications/`**: User notification system

### Infrastructure Apps
- **`entity/`**: Base entity models and utilities
- **`cachemodel/`**: Caching framework and utilities
- **`basic_models/`**: Shared base model classes
- **`badgrlog/`**: Logging and audit trail functionality
- **`staff/`**: Administrative dashboard and staff tools

### Integration Apps
- **`badgrsocialauth/`**: Social authentication providers (eduID, SURF Conext)
- **`mobile_api/`**: Mobile application API endpoints
- **`public/`**: Public-facing API endpoints
- **`ob3/`**: Open Badges 3.0 specification support

## File Structure Conventions

### Standard Django App Layout
```
apps/[app_name]/
├── __init__.py
├── models.py          # Database models
├── api.py             # API views and endpoints
├── serializers.py     # DRF serializers
├── permissions.py     # Permission classes
├── schema.py          # GraphQL schema definitions
├── admin.py           # Django admin configuration
├── migrations/        # Database migrations
└── tests/            # Test files
```

### URL Organization
- **`api_urls.py`**: REST API URL patterns
- **`urls.py`**: General URL patterns
- **`v1_api_urls.py`**: Versioned API URLs (legacy)

### Key Directories
- **`apps/mainsite/settings.py`**: Main Django settings
- **`apps/mainsite/templates/`**: Django templates
- **`apps/mainsite/static/`**: Static assets
- **`mediafiles/uploads/`**: User-uploaded files (badges, logos)
- **`queries/`**: Raw SQL queries for reporting
- **`scripts/`**: Utility scripts
- **`docker/`**: Docker configuration files

## Naming Conventions

### Models
- Use singular names: `BadgeClass`, `BadgeInstance`, `Institution`
- Follow Django conventions for field names
- Use `entity_id` for unique identifiers across apps

### API Endpoints
- RESTful naming: `/api/v2/badgeclasses/`, `/api/v2/issuers/`
- Use plural nouns for collections
- Consistent versioning in URL paths

### Files and Directories
- Use lowercase with underscores: `badge_user.py`, `direct_award/`
- Test files: `test_[functionality].py`
- Migration files: Auto-generated Django format

## Database Schema
- Each app manages its own models and migrations
- Shared functionality in `entity/` and `basic_models/`
- Foreign key relationships follow Django conventions
- Use UUIDs for public-facing identifiers
