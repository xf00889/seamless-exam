# Static Images and Icons

This directory contains all static images and icons used in the Offline Exam System.

## Files

### Default Avatar
- **default-avatar.svg** - Default profile picture shown when a student hasn't uploaded their own image
  - Size: 200x200px
  - Format: SVG (scalable, lightweight)
  - Colors: Gray tones (#e5e7eb, #9ca3af)

### Dashboard Metric Icons
Icons used in the student dashboard metric cards:

- **icon-total-exams.svg** - Document icon for total exams taken
- **icon-average-score.svg** - Bar chart icon for average score
- **icon-highest-score.svg** - Trophy icon for highest score achieved
- **icon-pass-rate.svg** - Check circle icon for pass rate percentage

### Profile & UI Icons
General purpose icons for profile and interface elements:

- **icon-user.svg** - User profile icon
- **icon-lock.svg** - Password/security icon
- **icon-calendar.svg** - Date/calendar icon
- **icon-upload.svg** - File upload icon
- **icon-download.svg** - Download/export icon
- **icon-edit.svg** - Edit/modify icon

## Usage

### In HTML Templates
```html
<!-- Default Avatar -->
<img src="{% static 'img/default-avatar.svg' %}" alt="Default Avatar" class="profile-picture">

<!-- Metric Card Icon -->
<div class="metric-card-icon blue">
    <img src="{% static 'img/icon-total-exams.svg' %}" alt="Total Exams">
</div>
```

### Icon Colors
All icons use `stroke="currentColor"` which means they inherit the text color from their parent element. This allows for easy color customization via CSS:

```css
.icon-container {
    color: #3b82f6; /* Blue */
}
```

## Optimization

All SVG files are:
- Minified (no unnecessary whitespace)
- Optimized for web delivery
- Lightweight (< 1KB each)
- Scalable without quality loss
- Accessible (proper viewBox and dimensions)

## Requirements Satisfied

- **Requirement 2.4**: Default avatar image for profile pictures
- **Requirement 7.5**: Icons for metric cards in dashboard
- **Requirement 13.1**: Secure, optimized image assets

## Adding New Icons

When adding new icons:
1. Use SVG format for scalability
2. Set viewBox="0 0 24 24" for consistency
3. Use stroke="currentColor" for color flexibility
4. Keep stroke-width="2" for visual consistency
5. Optimize file size by removing unnecessary attributes
6. Document the icon purpose in this README
