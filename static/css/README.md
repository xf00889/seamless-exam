# CSS Stylesheets

This directory contains all CSS stylesheets for the Offline Exam System.

## Files

### main.css
Core stylesheet with base styles used across the entire application:
- Button styles (primary, secondary, danger, success)
- Form styles (inputs, labels, error messages)
- Card styles
- Table styles
- Alert/notification styles

**Usage**: Included in base.html template, loaded on all pages.

### profile.css
Profile and dashboard specific styles:
- Profile picture components (container, overlay, sizes)
- Metric card styles with hover effects
- Chart container styles
- Profile information cards
- Password strength indicator
- Activity list styles
- Status badges
- Responsive grid layouts
- Loading states
- Empty state designs

**Usage**: Include in profile and dashboard pages only.

```html
{% load static %}
<link rel="stylesheet" href="{% static 'css/profile.css' %}">
```

## Design System

### Color Palette
- **Primary Blue**: #3b82f6, #2563eb, #1d4ed8
- **Success Green**: #16a34a, #15803d, #dcfce7
- **Danger Red**: #dc2626, #b91c1c, #fef2f2
- **Warning Amber**: #f59e0b, #d97706, #fef3c7
- **Purple**: #9333ea, #f3e8ff
- **Gray Scale**: #111827, #374151, #6b7280, #9ca3af, #e5e7eb, #f3f4f6, #f9fafb

### Typography
- **Headings**: Font weight 600-700
- **Body**: Font size 0.875rem (14px)
- **Labels**: Font size 0.875rem, weight 500
- **Meta text**: Font size 0.75rem (12px)

### Spacing
- **Card padding**: 1.5rem (24px)
- **Section margins**: 1.5rem (24px)
- **Element spacing**: 0.5rem - 1rem (8px - 16px)

### Border Radius
- **Cards**: 0.5rem (8px)
- **Buttons**: 0.375rem (6px)
- **Badges**: 9999px (fully rounded)
- **Profile pictures**: 50% (circular)

### Shadows
- **Default**: 0 1px 3px 0 rgba(0, 0, 0, 0.1)
- **Hover**: 0 4px 6px -1px rgba(0, 0, 0, 0.1)

## Responsive Breakpoints

```css
/* Mobile */
@media (max-width: 768px) {
    /* Tablet and below */
}

/* Desktop */
@media (min-width: 769px) {
    /* Desktop and above */
}
```

## Component Classes

### Metric Cards
```html
<div class="metric-card">
    <div class="metric-card-icon blue">
        <!-- Icon SVG -->
    </div>
    <div class="metric-card-value">85.5%</div>
    <div class="metric-card-label">Average Score</div>
</div>
```

### Profile Picture
```html
<div class="profile-picture-container">
    <img src="..." class="profile-picture" alt="Profile">
    <div class="profile-picture-upload-overlay">
        <!-- Upload icon -->
    </div>
</div>
```

### Status Badges
```html
<span class="status-badge graded">Graded</span>
<span class="status-badge pending">Pending</span>
<span class="status-badge in-progress">In Progress</span>
```

### Activity List
```html
<ul class="activity-list">
    <li class="activity-item">
        <div class="activity-icon"><!-- Icon --></div>
        <div class="activity-content">
            <div class="activity-title">Exam Title</div>
            <div class="activity-meta">Date and time</div>
        </div>
        <div class="activity-score pass">95%</div>
    </li>
</ul>
```

## Performance

- All CSS is vanilla CSS (no preprocessors required)
- Minified for production (if needed)
- No external dependencies
- Optimized for offline use
- Total size: < 20KB combined

## Browser Support

- Modern browsers (Chrome, Firefox, Safari, Edge)
- CSS Grid and Flexbox support required
- CSS Custom Properties (variables) not used for IE11 compatibility

## Requirements Satisfied

- **Requirement 12.1-12.5**: Responsive design for mobile and desktop
- **Requirement 7.5**: Visual styling for dashboard metrics
- **Requirement 2.4**: Profile picture styling
- **Offline-first**: No external CSS dependencies
