---
inclusion: always
---

# ExamMaker System Development Guide

This Django-based exam system is designed for offline local network deployment in educational environments with manual exam creation workflows. The system focuses on teacher-driven content creation without external dependencies. Follow these architectural patterns and conventions when working with the codebase.

## Table of Contents
- [Architecture Patterns](#architecture-patterns)
- [Database Conventions](#database-conventions)
- [Security Implementation](#security-implementation)
- [Local Network Deployment](#local-network-deployment)
- [Code Style](#code-style)
- [Testing Conventions](#testing-conventions)
- [Error Handling](#error-handling)
- [File Organization](#file-organization)

## Architecture Patterns

### Repository Pattern
- Use repositories for data access abstraction
- All repositories extend `BaseRepository` in `repositories/base_repository.py`
- Repository methods return Django model instances or QuerySets
- Handle database exceptions within repositories, return `None` for not found

**Example:**
```python
class ExamRepository(BaseRepository):
    def get_active_exams_for_teacher(self, teacher_id: int) -> QuerySet:
        try:
            return Exam.objects.filter(
                teacher_id=teacher_id, 
                is_active=True
            ).select_related('teacher')
        except DatabaseError:
            logger.error(f"Database error fetching exams for teacher {teacher_id}")
            return Exam.objects.none()
```

### Service Layer Pattern
- Business logic resides in service classes under `services/`
- Services orchestrate repositories and handle complex operations
- Use dependency injection for repository instances
- Services return domain objects, not database models directly

**Example:**
```python
class ExamService:
    def __init__(self, exam_repo: ExamRepository, student_repo: StudentRepository):
        self.exam_repo = exam_repo
        self.student_repo = student_repo
    
    @transaction.atomic
    def assign_exam_to_class(self, exam_id: int, class_id: int) -> Result:
        exam = self.exam_repo.get_by_id(exam_id)
        if not exam:
            return Result.failure("Exam not found")
        
        students = self.student_repo.get_by_class(class_id)
        # Business logic here
        return Result.success(assignment_data)
```

### Extractor Pattern
- Document processing uses abstract extractors under `processing/extractors/`
- All extractors implement `BaseExtractor` interface
- Support PDF and DOCX formats with consistent error handling
- Use factory pattern for extractor selection based on file type
- Extractors provide content for manual question creation workflows

## Database Conventions

### Model Design
- Use explicit `db_table` names following `app_modelname` pattern
- Add database indexes for frequently queried fields
- Use composite indexes for multi-field queries (performance optimization)
- Implement `__str__` methods for admin interface readability

### Field Patterns
- Use `JSONField` for flexible data storage (options, answers, parameters)
- Add `help_text` for complex fields
- Use `db_index=True` for foreign keys and frequently filtered fields
- Include `created_at` and `updated_at` timestamps where appropriate

### Relationships
- Use `related_name` for reverse relationships
- Implement proper `on_delete` behavior (CASCADE, SET_NULL, PROTECT)
- Add unique constraints for business rules (`unique_together`)

## Security Implementation

### Authentication
- Students authenticate with `school_id` and password
- Teachers use Django's built-in User model
- Password hashing uses Django's PBKDF2 with SHA256
- Session management with secure cookie settings

### File Upload Security
- Validate file extensions and MIME types
- Limit file sizes (50MB for documents, 5MB for images)
- Store uploads outside web root in `media/` directory
- Sanitize file names to prevent path traversal

### CSRF and XSS Protection
- Django CSRF middleware enabled with custom token names
- Template auto-escaping prevents XSS
- Secure session and CSRF cookie configurations

## Environment Configuration

### Required Environment Variables
```bash
# Security
SECRET_KEY=your-secret-key-here
CSRF_COOKIE_NAME=exammaker_csrftoken
SESSION_COOKIE_NAME=exammaker_sessionid

# File Upload
MAX_UPLOAD_SIZE=52428800  # 50MB
MAX_IMAGE_SIZE=5242880    # 5MB
```

### Development vs Production Settings
- Development: `DEBUG = True`, detailed error pages
- Production: `DEBUG = False`, custom error templates
- Use environment-specific settings files when needed

## Local Network Deployment

### Configuration
- SQLite database for simplicity (no external database server)
- `ALLOWED_HOSTS = ['*']` for local network access
- Static files served directly from Django
- No external dependencies (CDNs, APIs, cloud services, or AI services)
- Manual exam creation workflow only

### Deployment Checklist
- [ ] Run `python manage.py collectstatic` before deployment
- [ ] Ensure `DEBUG = False` in production
- [ ] Test file upload permissions in `media/` directory
- [ ] Confirm network accessibility from student devices

### Performance Optimization
- Database connection pooling with `CONN_MAX_AGE = 600`
- Composite database indexes for common query patterns
- Caching for dashboard metrics using database backend

## Code Style

### Python Conventions
- Follow PEP 8 style guidelines
- Use type hints for method parameters and return values
- Implement proper exception handling with specific exception types
- Use logging instead of print statements

### Django Patterns
- Use `@transaction.atomic` for multi-model operations
- Implement proper form validation in Django forms
- Use Django's built-in pagination for list views
- Follow Django's URL naming conventions

### JavaScript/Frontend
- Use vanilla JavaScript (no external frameworks)
- Implement progressive enhancement patterns
- Use SweetAlert2 for user notifications
- Follow mobile-first responsive design principles

## Testing Conventions

### Test Structure
- Use Django's TestCase for database-dependent tests
- Implement Hypothesis property-based testing for complex logic
- Test files follow `test_*.py` naming convention
- Use fixtures for test data setup

### Coverage Areas
- Repository layer unit tests
- Service layer business logic tests
- View integration tests with authentication
- Form validation tests

## Error Handling

### Logging Configuration
- Structured logging with different levels (DEBUG, INFO, ERROR)
- Separate log files for services, errors, and general application logs
- Rotating file handlers to prevent disk space issues
- Context-aware error messages with module and function names

### User-Facing Errors
- Use Django messages framework for user notifications
- Provide clear error messages for file upload issues
- Handle network connectivity problems in local deployment

## Troubleshooting

### Common Issues
- **File Upload Errors**: Verify `media/` directory permissions and disk space
- **Database Locked**: Ensure only one Django process accesses SQLite
- **Static Files Missing**: Run `python manage.py collectstatic`
- **Network Access Issues**: Check firewall settings and `ALLOWED_HOSTS`

### Debug Commands
```bash
# Verify database connectivity
python manage.py dbshell

# Test static file serving
python manage.py findstatic css/main.css
```

## File Organization

### Directory Structure
- `services/` - Business logic layer (manual exam creation services only)
- `repositories/` - Data access layer  
- `processing/` - Document processing and content extraction (for manual question creation)
- `static/` - CSS, JavaScript, images
- `templates/` - Django HTML templates
- `media/` - User uploaded files

### Naming Conventions
- Service classes: `*Service` (e.g., `ExamService`)
- Repository classes: `*Repository` (e.g., `ExamRepository`)
- Model classes: PascalCase (e.g., `ExamClassAssignment`)
- URL patterns: kebab-case (e.g., `exam-list`)

This system prioritizes offline functionality, security, manual content creation, and educational use cases. Always consider the local network deployment context and manual-only workflows when making architectural decisions.

## Quick Reference

### Common Commands
```bash
# Start development server
python manage.py runserver 0.0.0.0:8000

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic
```

### Key File Locations
- Models: `{app}/models.py`
- Views: `{app}/views.py`
- Templates: `templates/{app}/`
- Static files: `static/`
- Media uploads: `media/`
- Configuration: `exam_system/settings.py`