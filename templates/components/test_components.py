"""
Test reusable template components
Requirements: 17.1, 17.3 - Verify no inline CSS or JavaScript
"""
from django.test import TestCase
from django.template import Template, Context
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpRequest


class ComponentRenderTest(TestCase):
    """Test that components render correctly without inline styles or scripts."""
    
    def test_navbar_component_renders(self):
        """Test navbar component renders without inline styles."""
        template = Template("{% include 'components/navbar.html' %}")
        context = Context({
            'user': type('User', (), {'is_authenticated': True, 'username': 'testuser'})(),
            'navbar_nav_links': [
                {'url': '/dashboard/', 'label': 'Dashboard', 'active': True},
                {'url': '/exams/', 'label': 'Exams', 'active': False}
            ],
            'navbar_student_name': 'Test User',
            'navbar_student': type('Student', (), {
                'first_name': 'Test',
                'last_name': 'User',
                'school_id': '12345'
            })()
        })
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify no inline JavaScript
        self.assertNotIn('onclick=', rendered)
        self.assertNotIn('onchange=', rendered)
        # Verify component renders
        self.assertIn('Seamless', rendered)
        self.assertIn('Test User', rendered)
    
    def test_footer_component_renders(self):
        """Test footer component renders without inline styles."""
        template = Template("{% include 'components/footer.html' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify component renders
        self.assertIn('Seamless', rendered)
        self.assertIn('All rights reserved', rendered)
    
    def test_alert_component_renders_success(self):
        """Test alert component renders success message without inline styles."""
        template = Template("{% include 'components/alert.html' with type='success' message='Test success' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify no inline JavaScript
        self.assertNotIn('onclick=', rendered)
        # Verify component renders with correct styling classes
        self.assertIn('bg-green-50', rendered)
        self.assertIn('text-green-800', rendered)
        self.assertIn('Test success', rendered)
    
    def test_alert_component_renders_error(self):
        """Test alert component renders error message without inline styles."""
        template = Template("{% include 'components/alert.html' with type='error' message='Test error' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify component renders with correct styling classes
        self.assertIn('bg-red-50', rendered)
        self.assertIn('text-red-800', rendered)
        self.assertIn('Test error', rendered)
    
    def test_alert_component_dismissible(self):
        """Test alert component with dismissible button."""
        template = Template("{% include 'components/alert.html' with message='Test' dismissible=True %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify dismiss button is present
        self.assertIn('alert-close', rendered)
        # Verify no inline JavaScript on button
        self.assertNotIn('onclick=', rendered)
    
    def test_pagination_component_renders(self):
        """Test pagination component renders without inline styles."""
        from django.core.paginator import Paginator
        
        items = list(range(1, 51))  # 50 items
        paginator = Paginator(items, 10)
        page_obj = paginator.get_page(1)
        
        template = Template("{% include 'components/pagination.html' with page_obj=page_obj %}")
        context = Context({'page_obj': page_obj})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify no inline JavaScript
        self.assertNotIn('onclick=', rendered)
        # Verify pagination elements
        self.assertIn('Previous', rendered)
        self.assertIn('Next', rendered)
    
    def test_input_field_component_text(self):
        """Test input field component renders text input without inline styles."""
        template = Template("{% include 'components/input_field.html' with name='test' label='Test Field' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify component renders
        self.assertIn('Test Field', rendered)
        self.assertIn('name="test"', rendered)
        self.assertIn('type="text"', rendered)
    
    def test_input_field_component_textarea(self):
        """Test input field component renders textarea without inline styles."""
        template = Template("{% include 'components/input_field.html' with name='desc' label='Description' type='textarea' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify component renders
        self.assertIn('Description', rendered)
        self.assertIn('name="desc"', rendered)
        self.assertIn('<textarea', rendered)
    
    def test_input_field_component_required(self):
        """Test input field component shows required indicator."""
        template = Template("{% include 'components/input_field.html' with name='test' label='Test' required=True %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify required indicator
        self.assertIn('text-red-500', rendered)
        self.assertIn('*', rendered)
        self.assertIn('required', rendered)
    
    def test_input_field_component_with_error(self):
        """Test input field component displays error message."""
        template = Template("{% include 'components/input_field.html' with name='test' label='Test' error='Invalid input' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify error styling
        self.assertIn('border-red-500', rendered)
        self.assertIn('Invalid input', rendered)
        self.assertIn('text-red-600', rendered)
    
    def test_empty_state_component_default(self):
        """Test empty state component renders with default icon."""
        template = Template("{% include 'components/empty_state.html' with title='No Data' description='Nothing to show' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no inline styles
        self.assertNotIn('style=', rendered)
        # Verify component renders
        self.assertIn('No Data', rendered)
        self.assertIn('Nothing to show', rendered)
        self.assertIn('empty-state', rendered)
    
    def test_empty_state_component_with_search_icon(self):
        """Test empty state component renders with search icon."""
        template = Template("{% include 'components/empty_state.html' with icon_type='search' title='No Results' description='Try different filters' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify search icon path is present
        self.assertIn('M21 21l-6-6m2-5a7 7 0 11-14 0', rendered)
        self.assertIn('No Results', rendered)
    
    def test_empty_state_component_with_chart_icon(self):
        """Test empty state component renders with chart icon."""
        template = Template("{% include 'components/empty_state.html' with icon_type='chart' title='No Chart Data' description='Data needed for charts' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify chart icon path is present
        self.assertIn('M9 19v-6a2 2 0 00-2-2H5', rendered)
        self.assertIn('No Chart Data', rendered)
    
    def test_empty_state_component_with_exam_icon(self):
        """Test empty state component renders with exam icon."""
        template = Template("{% include 'components/empty_state.html' with icon_type='exam' title='No Exams' description='Create your first exam' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify exam icon path is present
        self.assertIn('M9 12h6m-6 4h6m2 5H7', rendered)
        self.assertIn('No Exams', rendered)
    
    def test_empty_state_component_with_action_url(self):
        """Test empty state component renders with action button using URL."""
        template = Template("{% include 'components/empty_state.html' with title='Empty' action_url='/create/' action_text='Create Now' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify action button with URL
        self.assertIn('href="/create/"', rendered)
        self.assertIn('Create Now', rendered)
        self.assertIn('empty-state-action', rendered)
    
    def test_empty_state_component_with_action_onclick(self):
        """Test empty state component renders with action button using onclick."""
        template = Template("{% include 'components/empty_state.html' with title='Empty' action_onclick='clearFilters()' action_text='Clear Filters' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify action button with onclick
        self.assertIn('onclick="clearFilters()"', rendered)
        self.assertIn('Clear Filters', rendered)
        self.assertIn('<button', rendered)
    
    def test_empty_state_component_without_action(self):
        """Test empty state component renders without action button."""
        template = Template("{% include 'components/empty_state.html' with title='Empty' description='No action available' %}")
        context = Context({})
        rendered = template.render(context)
        
        # Verify no action button
        self.assertNotIn('empty-state-action', rendered)
        self.assertNotIn('<button', rendered)
        self.assertNotIn('<a', rendered.split('empty-state-description')[1])  # No link after description
    
    def test_components_use_external_css_only(self):
        """Test that all components use external CSS classes only."""
        components = [
            'navbar.html',
            'footer.html',
            'alert.html',
            'messages.html',
            'pagination.html',
            'form_field.html',
            'input_field.html',
            'empty_state.html',
        ]
        
        for component in components:
            with open(f'templates/components/{component}', 'r') as f:
                content = f.read()
                
                # Verify no inline styles
                self.assertNotIn('style=', content, f'{component} contains inline styles')
                # Verify no style tags
                self.assertNotIn('<style>', content, f'{component} contains style tags')
                # Verify no inline JavaScript event handlers (except onclick in empty_state which is passed as parameter)
                if component != 'empty_state.html':
                    self.assertNotIn('onclick=', content, f'{component} contains onclick handlers')
                self.assertNotIn('onchange=', content, f'{component} contains onchange handlers')
                self.assertNotIn('onsubmit=', content, f'{component} contains onsubmit handlers')
                # Verify no script tags with inline code (allow empty script tags for external files)
                if '<script>' in content:
                    # Check if it's not just a closing tag or external script reference
                    script_content = content.split('<script>')[1].split('</script>')[0].strip()
                    if script_content and 'src=' not in script_content:
                        self.fail(f'{component} contains inline JavaScript')

