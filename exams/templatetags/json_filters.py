"""
Custom template filters for JSON serialization
"""
import json
from django import template
from django.utils.safestring import mark_safe
from django.contrib.messages import get_messages

register = template.Library()


@register.filter(name='to_json')
def to_json(value):
    """
    Convert a Python object to JSON string.
    Useful for passing data to JavaScript via data attributes.
    """
    if value is None:
        return 'null'
    
    try:
        return mark_safe(json.dumps(value))
    except (TypeError, ValueError):
        return 'null'


@register.filter(name='messages_to_json')
def messages_to_json(messages):
    """
    Convert Django messages to JSON string.
    Handles the FallbackStorage serialization issue.
    """
    if not messages:
        return 'null'
    
    try:
        # Convert messages to a list of dictionaries
        messages_list = []
        for message in messages:
            messages_list.append({
                'text': str(message),  # JavaScript expects 'text' not 'message'
                'type': message.level_tag,  # JavaScript expects 'type' not 'tags'
                'tags': message.tags,
                'level': message.level,
                'level_tag': message.level_tag,
            })
        
        return mark_safe(json.dumps(messages_list))
    except (TypeError, ValueError, AttributeError):
        return 'null'
