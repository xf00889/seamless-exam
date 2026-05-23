# AI Removal Design Document

## Overview

This design outlines the systematic removal of all AI-powered exam generation functionality from the ExamMaker system. The system currently integrates with Ollama for automatic question generation through multiple service layers, database models, UI components, and configuration files. This removal will simplify the system architecture, eliminate external AI dependencies, and focus the application purely on manual exam creation workflows.

The removal process must preserve all existing manually created exam data while ensuring no AI-related code, configuration, or UI elements remain in the system.

## Architecture

### Current AI Integration Points

The system currently has AI integration across multiple layers:

1. **Service Layer**: AI question generation services, Ollama client, error handlers
2. **Database Layer**: AI metadata fields in Exam and Question models
3. **UI Layer**: AI generation forms, buttons, and status indicators
4. **Configuration Layer**: Ollama settings, model configurations
5. **Processing Layer**: AI-powered question generators
6. **Testing Layer**: AI service tests and mocks

### Target Architecture

After removal, the system will have:

1. **Simplified Service Layer**: Only manual question creation services
2. **Clean Database Models**: No AI-related fields or metadata
3. **Streamlined UI**: Manual-only exam creation workflows
4. **Minimal Configuration**: No AI-related settings
5. **Pure Processing**: Document extraction without AI generation
6. **Focused Testing**: Tests for manual workflows only

## Components and Interfaces

### Components to Remove

#### Service Layer Components
- `services/ai_question_generation_service.py` - Main AI generation orchestrator
- `services/ai_generation_models.py` - AI data models and validation
- `services/ai_error_handler.py` - AI-specific error handling
- `services/ollama_client.py` - HTTP client for Ollama API
- `services/ollama_config.py` - Ollama configuration management
- `services/ollama_service.py` - High-level Ollama service wrapper
- `services/prompt_builder.py` - AI prompt construction

#### Processing Layer Components
- `processing/generators/question_generator.py` - AI question generator
- AI-related methods in `processing/generators/` modules
- AI generation logic in `services/document_processing_service.py`

#### Test Components
- `services/test_ai_*.py` - All AI service tests
- `test_qwen25_model.py` - Model testing script
- `quick_test_llama32.py` - Quick AI testing script

#### Configuration Files
- AI-related environment variables in documentation
- Ollama configuration sections in settings

### Components to Modify

#### Database Models (`exams/models.py`)
- Remove `ai_generated` field from Exam model
- Remove `ai_model_used` field from Exam model  
- Remove `ai_generation_params` field from Exam model
- Remove `generation_timestamp` field from Exam model
- Remove `ai_generated` field from Question model

#### Views (`exams/views.py`)
- Remove AI generation handling in exam creation
- Remove AI-related imports
- Simplify exam creation workflow to manual-only

#### Templates
- Remove AI generation forms and buttons
- Remove AI status indicators and metadata displays
- Simplify exam creation UI

#### Services
- Remove AI-related methods from `services/dashboard_service.py`
- Remove AI audit logging from `services/audit_logger.py`
- Clean AI references from `services/exam_metadata_service.py`

### Interfaces to Preserve

#### Manual Exam Creation Interface
- Question entry forms for all question types (MCQ, Identification, Enumeration, Essay, True/False)
- File upload for questionnaires and answer keys
- Exam metadata management (title, subject, duration, etc.)
- Question editing and management

#### Document Processing Interface
- Document extraction from PDF and DOCX files
- Text cleaning and formatting
- Manual question creation from extracted content

## Data Models

### Database Schema Changes

#### Exam Model Changes
```python
# Fields to remove:
ai_generated = models.BooleanField(default=False)
ai_model_used = models.CharField(max_length=100, blank=True, null=True)
ai_generation_params = models.JSONField(blank=True, null=True)
generation_timestamp = models.DateTimeField(blank=True, null=True)
```

#### Question Model Changes
```python
# Fields to remove:
ai_generated = models.BooleanField(default=False)
```

#### Migration Strategy
- Create migration to remove AI-related fields
- Preserve all existing exam and question data
- Ensure no data loss during field removal
- Update any indexes that reference removed fields

### Data Preservation
- All manually created exams and questions will be preserved
- Exam functionality (taking, grading, statistics) remains unchanged
- Student and teacher data unaffected
- Historical exam results maintained

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After reviewing all properties identified in the prework, several can be consolidated:

- Properties 1.2, 3.3, and 3.5 all relate to code cleanliness and can be combined into a comprehensive "no AI references" property
- Properties 2.3, 4.1, 4.2, 4.3, and 4.4 all relate to functional preservation and can be combined into a "functionality preservation" property
- Properties 1.4, 2.1, 2.2, 2.4, and 2.5 are all UI-related examples that don't need separate properties

### Core Properties

**Property 1: AI Code Elimination**
*For any* file in the codebase, searching for AI-related terms (ollama, ai_, AI_, llama, OLLAMA) should return no matches in active code
**Validates: Requirements 1.2, 3.3, 3.5**

**Property 2: Functional Preservation**
*For any* existing manually created exam, all core functionality (display, taking, grading, statistics) should work identically to before AI removal
**Validates: Requirements 4.1, 4.2, 4.3, 4.4**

**Property 3: Data Integrity**
*For any* database migration operation, all existing exam and question data should be preserved without loss
**Validates: Requirements 4.5**

**Property 4: Manual Question Storage**
*For any* newly created question, the stored data should contain no AI-related metadata fields
**Validates: Requirements 2.3**

## Error Handling

### Error Scenarios During Removal

1. **Database Migration Errors**
   - Handle cases where AI fields are referenced by constraints
   - Manage foreign key dependencies
   - Provide rollback capability

2. **Import Errors**
   - Handle missing imports after AI service removal
   - Update all import statements referencing removed modules
   - Ensure no circular dependencies remain

3. **Template Rendering Errors**
   - Handle template variables referencing removed AI fields
   - Update template logic that depends on AI functionality
   - Ensure graceful degradation of UI components

4. **Configuration Errors**
   - Handle missing AI configuration gracefully
   - Remove AI-related settings validation
   - Update default configurations

### Error Recovery

- Provide clear error messages during migration
- Implement rollback procedures for failed removals
- Maintain system stability throughout removal process
- Ensure no breaking changes to existing functionality

## Testing Strategy

### Dual Testing Approach

The removal process requires both unit testing and property-based testing:

**Unit Tests:**
- Test specific removal operations (file deletion, import updates)
- Test database migration success
- Test UI component removal
- Test configuration cleanup

**Property-Based Tests:**
- Verify no AI references remain across all files
- Test functional preservation across all existing exams
- Verify data integrity across all database operations
- Test manual question creation across all question types

### Property-Based Testing Framework

We will use **Hypothesis** for Python property-based testing, configured to run a minimum of 100 iterations per property test.

Each property-based test will be tagged with comments referencing the design document:
- **Feature: ai-removal, Property 1: AI Code Elimination**
- **Feature: ai-removal, Property 2: Functional Preservation**
- **Feature: ai-removal, Property 3: Data Integrity**
- **Feature: ai-removal, Property 4: Manual Question Storage**

### Testing Phases

1. **Pre-Removal Testing**: Establish baseline functionality
2. **Incremental Testing**: Test each removal step
3. **Post-Removal Testing**: Verify complete removal and functionality
4. **Regression Testing**: Ensure no existing features broken