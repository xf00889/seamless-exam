# Reusable Template Components

This directory contains reusable Django template components that follow the project's requirements for external CSS only (Requirements 17.1, 17.3). All components use Tailwind CSS classes and external JavaScript files.

## Components

### 1. Navbar Component (`navbar.html`)

Displays the navigation bar with user information and logout link.

**Usage:**
```django
{% include 'components/navbar.html' %}
```

**Optional Parameters:**
- `nav_links`: List of navigation links with `url`, `label`, and `active` properties

**Example with nav links:**
```django
{% include 'components/navbar.html' with nav_links=nav_links %}
```

Where `nav_links` in your view context:
```python
nav_links = [
    {'url': '/exams/', 'label': 'Exams', 'active': True},
    {'url': '/dashboard/', 'label': 'Dashboard', 'active': False},
]
```

---

### 2. Footer Component (`footer.html`)

Displays the page footer with copyright information.

**Usage:**
```django
{% include 'components/footer.html' %}
```

**Optional Parameters:**
- `footer_links`: List of footer links with `url` and `label` properties

**Example with footer links:**
```django
{% include 'components/footer.html' with footer_links=footer_links %}
```

---

### 3. Alert Component (`alert.html`)

Displays a single alert message with optional icon and dismiss button.

**Usage:**
```django
{% include 'components/alert.html' with type='success' message='Operation completed successfully' dismissible=True %}
```

**Parameters:**
- `message` (required): The message text to display
- `type` (optional): Alert type - 'success', 'error', 'warning', 'info' (default: 'info')
- `dismissible` (optional): Boolean, whether to show close button (default: False)
- `icon` (optional): Boolean, whether to show icon (default: True)

**Examples:**
```django
{# Success message with dismiss button #}
{% include 'components/alert.html' with type='success' message='Exam created successfully!' dismissible=True %}

{# Error message #}
{% include 'components/alert.html' with type='error' message='Invalid credentials' %}

{# Warning without icon #}
{% include 'components/alert.html' with type='warning' message='Session will expire soon' icon=False %}

{# Info message #}
{% include 'components/alert.html' with message='Please complete all fields' %}
```

---

### 4. Messages Component (`messages.html`)

Displays Django messages framework messages using the alert component.

**Usage:**
```django
{% include 'components/messages.html' %}
```

This component automatically renders all messages from Django's messages framework. No parameters needed.

**In your view:**
```python
from django.contrib import messages

messages.success(request, 'Exam created successfully!')
messages.error(request, 'Invalid credentials')
messages.warning(request, 'Session will expire soon')
messages.info(request, 'Please complete all fields')
```

---

### 5. Pagination Component (`pagination.html`)

Displays pagination controls for paginated querysets.

**Usage:**
```django
{% include 'components/pagination.html' with page_obj=page_obj %}
```

**Parameters:**
- `page_obj` (required): Django paginator page object
- `show_page_info` (optional): Boolean, whether to show "Page X of Y" text (default: True)
- `show_count` (optional): Boolean, whether to show total count (default: True)

**Example in view:**
```python
from django.core.paginator import Paginator

def exam_list(request):
    exams = Exam.objects.all()
    paginator = Paginator(exams, 10)  # 10 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'exams/exam_list.html', {'page_obj': page_obj})
```

**Example in template:**
```django
{% for exam in page_obj %}
    {# Display exam #}
{% endfor %}

{% include 'components/pagination.html' with page_obj=page_obj %}
```

---

### 6. Form Field Component (`form_field.html`)

Renders a Django form field with label, input, help text, and error messages.

**Usage:**
```django
{% include 'components/form_field.html' with field=form.field_name %}
```

**Parameters:**
- `field` (required): Django form field
- `label` (optional): Custom label text (defaults to field.label)
- `required` (optional): Boolean, whether to show required indicator (defaults to field.field.required)
- `help_text` (optional): Custom help text (defaults to field.help_text)
- `placeholder` (optional): Placeholder text

**Examples:**
```django
{# Basic usage #}
{% include 'components/form_field.html' with field=form.title %}

{# With custom label #}
{% include 'components/form_field.html' with field=form.title label='Exam Title' %}

{# With placeholder #}
{% include 'components/form_field.html' with field=form.email placeholder='Enter your email' %}

{# Complete form example #}
<form method="post">
    {% csrf_token %}
    {% include 'components/form_field.html' with field=form.title %}
    {% include 'components/form_field.html' with field=form.description %}
    {% include 'components/form_field.html' with field=form.duration_minutes %}
    <button type="submit">Submit</button>
</form>
```

---

### 7. Input Field Component (`input_field.html`)

Renders a standalone input field (for non-Django forms or custom forms).

**Usage:**
```django
{% include 'components/input_field.html' with name='email' label='Email Address' type='email' required=True %}
```

**Parameters:**
- `name` (required): Input name attribute
- `label` (required): Label text
- `type` (optional): Input type (default: 'text', can be 'textarea', 'select', 'checkbox', etc.)
- `value` (optional): Current value
- `placeholder` (optional): Placeholder text
- `required` (optional): Boolean, whether field is required (default: False)
- `help_text` (optional): Help text to display below field
- `error` (optional): Error message to display
- `options` (optional): List of options for select fields
- `rows` (optional): Number of rows for textarea (default: 3)
- `min`, `max`, `step` (optional): Attributes for number inputs

**Examples:**
```django
{# Text input #}
{% include 'components/input_field.html' with name='username' label='Username' required=True %}

{# Email input with placeholder #}
{% include 'components/input_field.html' with name='email' label='Email' type='email' placeholder='user@example.com' %}

{# Textarea #}
{% include 'components/input_field.html' with name='description' label='Description' type='textarea' rows=5 %}

{# Select dropdown #}
{% include 'components/input_field.html' with name='status' label='Status' type='select' options=status_options %}

{# Number input with min/max #}
{% include 'components/input_field.html' with name='duration' label='Duration (minutes)' type='number' min=1 max=180 %}

{# Checkbox #}
{% include 'components/input_field.html' with name='is_active' label='Active' type='checkbox' value=True %}

{# With error message #}
{% include 'components/input_field.html' with name='email' label='Email' error='Invalid email format' %}

{# With help text #}
{% include 'components/input_field.html' with name='password' label='Password' type='password' help_text='Must be at least 8 characters' %}
```

---

## JavaScript Functionality

The components use external JavaScript from `static/js/main.js`:

- **Alert Dismissal**: Dismissible alerts can be closed by clicking the close button
- **Auto-hide**: Alerts automatically fade out after 5 seconds
- **Form Validation**: Basic client-side validation for required fields

---

## Styling

All components use Tailwind CSS classes from `static/css/tailwind.min.css`. No inline styles are used, adhering to Requirements 17.1 and 17.3.

### Color Schemes

- **Success**: Green (bg-green-50, text-green-800)
- **Error**: Red (bg-red-50, text-red-800)
- **Warning**: Yellow (bg-yellow-50, text-yellow-800)
- **Info**: Blue (bg-blue-50, text-blue-800)

---

## Best Practices

1. **Always use components instead of duplicating markup** - This ensures consistency and maintainability
2. **Pass context variables explicitly** - Use `with` keyword to pass parameters
3. **Validate required parameters** - Components check for required parameters and handle missing ones gracefully
4. **Use Django forms when possible** - The `form_field.html` component integrates seamlessly with Django forms
5. **Keep components simple** - Each component has a single responsibility

---

## Examples in Context

### Complete Page Example

```django
{% extends 'base.html' %}

{% block content %}
<div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-900">Create Exam</h2>
</div>

{# Show success/error messages #}
{% include 'components/messages.html' %}

<div class="bg-white shadow rounded-lg p-6">
    <form method="post">
        {% csrf_token %}
        
        {% include 'components/form_field.html' with field=form.title %}
        {% include 'components/form_field.html' with field=form.description %}
        {% include 'components/form_field.html' with field=form.duration_minutes %}
        
        <div class="flex justify-end space-x-3">
            <a href="{% url 'exam_list' %}" class="px-4 py-2 border border-gray-300 rounded-md">
                Cancel
            </a>
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md">
                Create
            </button>
        </div>
    </form>
</div>
{% endblock %}
```

### List with Pagination Example

```django
{% extends 'base.html' %}

{% block content %}
<div class="mb-6">
    <h2 class="text-2xl font-bold text-gray-900">Exams</h2>
</div>

{% if page_obj %}
<div class="bg-white shadow rounded-lg">
    <table class="min-w-full">
        <thead>
            <tr>
                <th>Title</th>
                <th>Duration</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {% for exam in page_obj %}
            <tr>
                <td>{{ exam.title }}</td>
                <td>{{ exam.duration_minutes }} min</td>
                <td>{{ exam.get_status_display }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>

{% include 'components/pagination.html' with page_obj=page_obj %}
{% else %}
{% include 'components/alert.html' with type='info' message='No exams found' %}
{% endif %}
{% endblock %}
```

---

## Requirements Compliance

These components satisfy the following requirements:

- **Requirement 17.1**: All CSS is loaded from external Tailwind files
- **Requirement 17.3**: No inline CSS styles in HTML templates
- **Requirement 17.2**: All JavaScript is in external files
- **Requirement 17.4**: No inline JavaScript in HTML templates

All components are designed to work offline (Requirement 18.4) with locally served assets.
