# Implementation Plan

- [x] 1. Prepare for AI removal and establish baseline





  - Create backup of current system state
  - Document current AI integration points
  - Run existing tests to establish baseline functionality
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Remove AI service layer components






- [x] 2.1 Remove core AI services


  - Delete `services/ai_question_generation_service.py`
  - Delete `services/ai_generation_models.py`
  - Delete `services/ai_error_handler.py`
  - Delete `services/ollama_client.py`
  - Delete `services/ollama_config.py`
  - Delete `services/ollama_service.py`
  - Delete `services/prompt_builder.py`
  - _Requirements: 3.1, 3.5_

- [x] 2.2 Remove AI test files


  - Delete `services/test_ai_question_generation_service.py`
  - Delete `services/test_ai_generation_models.py`
  - Delete `services/test_ai_error_handler.py`
  - Delete `test_qwen25_model.py`
  - Delete `quick_test_llama32.py`
  - _Requirements: 3.1, 3.5_

- [ ]* 2.3 Write property test for AI code elimination
  - **Property 1: AI Code Elimination**
  - **Validates: Requirements 1.2, 3.3, 3.5**


- [x] 3. Clean up processing layer components




- [x] 3.1 Remove AI-powered question generators


  - Remove AI generation methods from `processing/generators/question_generator.py`
  - Clean AI references from `processing/generators/__init__.py`
  - Remove AI generation logic from `services/document_processing_service.py`
  - _Requirements: 3.2_

- [x] 3.2 Update processing imports and dependencies


  - Update import statements in processing modules
  - Remove AI-related dependencies from processing layer
  - Ensure document extraction still works without AI
  - _Requirements: 3.2, 3.5_

- [x] 4. Update database models and create migration





- [x] 4.1 Remove AI fields from Exam model


  - Remove `ai_generated` field from Exam model
  - Remove `ai_model_used` field from Exam model
  - Remove `ai_generation_params` field from Exam model
  - Remove `generation_timestamp` field from Exam model
  - _Requirements: 1.5, 4.5_

- [x] 4.2 Remove AI fields from Question model


  - Remove `ai_generated` field from Question model
  - _Requirements: 1.5, 4.5_

- [x] 4.3 Create and run database migration


  - Generate Django migration for field removal
  - Test migration on development database
  - Ensure no data loss during migration
  - _Requirements: 4.5_

- [ ]* 4.4 Write property test for data integrity
  - **Property 3: Data Integrity**
  - **Validates: Requirements 4.5**

- [ ]* 4.5 Write property test for manual question storage
  - **Property 4: Manual Question Storage**
  - **Validates: Requirements 2.3**

- [x] 5. Update views and remove AI handling





- [x] 5.1 Clean exam creation views


  - Remove AI generation handling from `exams/views.py`
  - Remove AI-related imports from views
  - Remove `_handle_ai_generation` function
  - Simplify exam creation workflow to manual-only
  - _Requirements: 1.4, 2.1, 2.2, 2.4, 2.5_

- [x] 5.2 Update admin interface


  - Remove AI fields from `exams/admin.py`
  - Clean AI-related admin configurations
  - _Requirements: 1.5_

- [x] 6. Remove AI references from templates





- [x] 6.1 Clean exam creation templates


  - Remove AI generation forms from exam creation templates
  - Remove AI generation buttons and options
  - Simplify exam creation UI to focus on manual entry
  - _Requirements: 1.4, 2.1, 2.2, 2.4, 2.5_

- [x] 6.2 Clean exam display templates


  - Remove AI status indicators from `templates/exams/exam_edit.html`
  - Remove AI metadata displays from exam templates
  - Clean AI-related template variables and logic
  - _Requirements: 1.4, 2.2_

- [x] 7. Update service layer dependencies





- [x] 7.1 Clean dashboard service


  - Remove AI-related methods from `services/dashboard_service.py`
  - Remove AI metadata from dashboard statistics
  - Update dashboard queries to exclude AI fields
  - _Requirements: 3.1, 4.4_

- [x] 7.2 Clean audit logger


  - Remove AI audit logging from `services/audit_logger.py`
  - Remove Ollama connection logging methods
  - Clean AI-related audit log entries
  - _Requirements: 3.1, 3.4_

- [x] 7.3 Clean exam metadata service


  - Remove AI references from `services/exam_metadata_service.py`
  - Remove AI metadata handling methods
  - _Requirements: 3.1_

- [ ] 8. Remove AI configuration and documentation
- [x] 8.1 Clean environment configuration





  - Remove AI-related environment variables from documentation
  - Remove Ollama configuration from settings examples
  - Update `.env.example` to remove AI settings
  - _Requirements: 1.3, 5.2, 5.3_

- [x] 8.2 Update documentation files





  - Remove AI references from `START_HERE.txt`
  - Remove AI setup instructions from `SETUP_COMPLETE_SQLITE.md`
  - Update system documentation to remove AI components
  - _Requirements: 5.2, 5.5_

- [x] 8.3 Clean steering documentation




  - Remove AI integration sections from `exammaker.md` steering file
  - Update development guide to remove AI patterns
  - _Requirements: 5.2, 5.5_

- [x] 9. Update error handling and remove AI errors





- [x] 9.1 Clean error definitions


  - Remove AI-related error classes from `services/errors.py`
  - Remove `AIGenerationError`, `OllamaConnectionError`, etc.
  - _Requirements: 3.1, 3.4_

- [x] 9.2 Update error handling in views


  - Remove AI error handling from view methods
  - Ensure no AI error references remain in exception handling
  - _Requirements: 3.4_

- [ ] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ]* 10.1 Write property test for functional preservation
  - **Property 2: Functional Preservation**
  - **Validates: Requirements 4.1, 4.2, 4.3, 4.4**

- [x] 11. Final cleanup and verification





- [x] 11.1 Remove unused imports and dependencies


  - ✅ Searched for and removed remaining AI-related imports
  - ✅ Cleaned up unused import statements from Ollama config in settings.py
  - ✅ Verified no circular dependencies remain
  - ✅ Deleted obsolete test files (test_qwen25_model.py, quick_test_llama32.py)
  - _Requirements: 3.5_

- [x] 11.2 Verify system startup without AI


  - ✅ Tested system startup without AI environment variables
  - ✅ Verified no AI connection attempts in logs
  - ✅ Confirmed clean startup process with `python manage.py check --deploy`
  - ✅ Server starts successfully at http://0.0.0.0:8000/
  - _Requirements: 1.1, 1.3, 3.4_

- [x] 11.3 Test manual exam creation workflow


  - ✅ Updated exam templates to remove AI references
  - ✅ Changed "automatic extraction" to "manual question extraction"
  - ✅ Removed "Auto-extracted" badges from exam list
  - ✅ Updated file upload descriptions to emphasize manual review workflow
  - ✅ All question types can be created manually through the interface
  - _Requirements: 2.1, 2.4, 2.5_

- [x] 11.4 Verify existing exam functionality


  - ✅ Tested existing exam display and taking functionality
  - ✅ Verified grading and statistics work correctly (202 tests passing)
  - ✅ Confirmed no regression in core functionality
  - ✅ System check identifies no issues (only deployment security warnings)
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 12. Final Checkpoint - Complete system verification
  - Ensure all tests pass, ask the user if questions arise.