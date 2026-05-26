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
    Convert Django messages to a Python list for use with json_script filter.
    Returns a list of dicts (not a JSON string) so json_script can serialize it once.
    """
    if not messages:
        return []

    try:
        messages_list = []
        for message in messages:
            messages_list.append({
                'text': str(message),
                'type': message.level_tag,
                'tags': message.tags,
                'level': message.level,
                'level_tag': message.level_tag,
            })

        return messages_list
    except (TypeError, ValueError, AttributeError):
        return []
