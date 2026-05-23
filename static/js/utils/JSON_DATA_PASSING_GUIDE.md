# JSON Data Passing Implementation Guide

This guide explains how to implement JSON data passing from Django templates to JavaScript using the new JsonDataLoader utility.

## Overview

The JSON data passing system replaces inline JavaScript variables with structured JSON script tags, improving security, maintainability, and performance.

## Template Implementation

### 1. Add JSON Script Tags

In your Django template, add JSON script tags for data that needs to be passed to JavaScript:

```html
<!-- URL Configuration Data -->
{{ profile_urls|json_script:"profile-urls-data" }}

<!-- Form Configuration Data -->
{{ form_config|json_script:"form-config-data" }}

<!-- Chart Data -->
{{ chart_data|json_script:"chart-data" }}
```

### 2. Use JsonDataLoader in JavaScript

Use the JsonDataLoader utility to parse and use the JSON data:

```html
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Load single data source
    JsonDataLoader.loadData('profile-urls-data', function(urlsData) {
        // Use the data
        console.log(urlsData);
    });
    
    // Load multiple data sources
    JsonDataLoader.loadMultipleData({
        urls: 'profile-urls-data',
        config: 'form-config-data',
        charts: 'chart-data'
    }, function(data) {
        // data.urls, data.config, data.charts are available
        console.log(data);
    });
    
    // Apply configuration to components
    JsonDataLoader.applyConfiguration('form-config-data', window.FormValidator, 'setGlobalConfig');
    
    // Set up URL data attributes
    JsonDataLoader.loadData('profile-urls-data', function(urlsData) {
        JsonDataLoader.setupUrlDataAttributes({
            'profile-picture-form': {
                uploadUrl: urlsData.upload_url
            },
            'delete-picture-btn': {
                deleteUrl: urlsData.delete_url
            }
        });
    });
});
</script>
```

## Django View Implementation

### 1. Profile URLs Example

```python
def teacher_profile(request):
    context = {
        'teacher': teacher,
        'profile_urls': {
            'upload_url': reverse('teacher_profile_picture_upload'),
            'delete_url': reverse('teacher_profile_picture_upload'),
        }
    }
    return render(request, 'users/teacher_profile.html', context)
```

### 2. Form Configuration Example

```python
def student_account_management(request):
    context = {
        'form_config': {
            'validation': {
                'password_min_length': 8,
                'required_fields': ['first_name', 'last_name', 'school_id'],
                'patterns': {
                    'school_id': r'^\d{4,10}$'
                }
            },
            'urls': {
                'create_student': reverse('student_create'),
                'validate_school_id': reverse('validate_school_id')
            }
        }
    }
    return render(request, 'users/student_account_management.html', context)
```

### 3. Modal Configuration Example

```python
def class_list(request):
    context = {
        'classes': classes,
        'modal_config': {
            'delete_confirmation': {
                'title': 'Delete Class',
                'message': 'Are you sure you want to delete this class?',
                'confirm_text': 'Delete',
                'cancel_text': 'Cancel',
                'confirm_class': 'btn-danger',
                'require_password': True
            }
        }
    }
    return render(request, 'users/class_list.html', context)
```

### 4. Dashboard Configuration Example

```python
def teacher_dashboard(request):
    context = {
        'exam_performance_json': exam_performance_data,
        'passing_rate_json': passing_rate_data,
        'dashboard_config': {
            'chart_options': {
                'responsive': True,
                'animation': {'duration': 1000}
            },
            'refresh_interval': 30000,
            'auto_refresh': True
        }
    }
    return render(request, 'attempts/teacher_dashboard.html', context)
```

## JavaScript Component Integration

### 1. Form Validator Integration

```javascript
// In your form validator component
class FormValidator {
    static setGlobalConfig(config) {
        this.globalConfig = config;
        // Apply validation rules, patterns, etc.
    }
}
```

### 2. Modal Manager Integration

```javascript
// In your modal manager component
class ModalManager {
    static setConfig(config) {
        this.config = config;
        // Apply modal configurations
    }
}
```

### 3. Chart Component Integration

```javascript
// In your chart component
class DashboardCharts {
    static init(config) {
        // Use chart data and configuration
        this.initializeCharts(config);
    }
}
```

## Benefits

1. **Security**: No inline JavaScript with template variables
2. **Maintainability**: Centralized data passing mechanism
3. **Performance**: Better caching and minification support
4. **Debugging**: Easier to debug JSON data vs inline variables
5. **Standards**: Follows Django best practices for static files

## Migration from Inline Variables

### Before (Inline Variables)
```html
<script>
const uploadUrl = '{% url "profile_upload" %}';
const config = {
    minLength: {{ min_length }},
    required: {{ required_fields|safe }}
};
</script>
```

### After (JSON Data Passing)
```html
{{ profile_config|json_script:"profile-config-data" }}
<script>
JsonDataLoader.loadData('profile-config-data', function(config) {
    // Use config data
});
</script>
```

## Error Handling

The JsonDataLoader includes built-in error handling:

- Logs warnings for missing JSON script elements
- Logs errors for malformed JSON data
- Gracefully handles missing components or methods
- Provides fallback behavior when data is unavailable

## Best Practices

1. **Consistent Naming**: Use descriptive, consistent names for JSON script element IDs
2. **Data Structure**: Keep JSON data structures flat and simple when possible
3. **Error Handling**: Always handle cases where data might be missing
4. **Performance**: Only pass data that JavaScript actually needs
5. **Security**: Validate and sanitize data in Django views before passing to templates