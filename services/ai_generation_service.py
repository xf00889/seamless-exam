import os
import json
import time
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

QUESTION_TYPE_CONFIGS = {
    'MCQ': {
        'description': 'Multiple Choice Question with 4 options (A, B, C, D)',
        'format': '{"type": "MCQ", "question": "...", "options": [{"key": "A", "value": "..."}, {"key": "B", "value": "..."}, {"key": "C", "value": "..."}, {"key": "D", "value": "..."}], "correct_answer": "A", "points": 2}',
    },
    'TRUE_FALSE': {
        'description': 'True or False question',
        'format': '{"type": "TRUE_FALSE", "question": "...", "correct_answer": true, "points": 1}',
    },
    'IDENTIFICATION': {
        'description': 'Short answer identification question',
        'format': '{"type": "IDENTIFICATION", "question": "...", "correct_answer": ["acceptable answer 1", "acceptable answer 2"], "points": 2}',
    },
    'ENUMERATION': {
        'description': 'List/enumerate items question',
        'format': '{"type": "ENUMERATION", "question": "...", "correct_answer": {"items": ["item1", "item2", "item3"], "min_required": 3}, "points": 3}',
    },
    'ESSAY': {
        'description': 'Essay question (no correct answer, manually graded)',
        'format': '{"type": "ESSAY", "question": "...", "correct_answer": null, "points": 5}',
    },
}

FREE_MODELS = [
    {'id': 'deepseek/deepseek-r1-0528:free', 'name': 'DeepSeek R1 (Free)'},
    {'id': 'meta-llama/llama-4-scout:free', 'name': 'Llama 4 Scout (Free)'},
    {'id': 'google/gemma-3-27b-it:free', 'name': 'Google Gemma 3 27B (Free)'},
    {'id': 'qwen/qwen3-8b:free', 'name': 'Qwen 3 8B (Free)'},
    {'id': 'mistralai/mistral-small-3.1-24b-instruct:free', 'name': 'Mistral Small 3.1 24B (Free)'},
    {'id': 'meta-llama/llama-4-maverick:free', 'name': 'Llama 4 Maverick (Free)'},
]


def get_ai_config():
    """Get AI configuration from database settings or environment."""
    try:
        from users.models import SystemSettings
        settings_obj = SystemSettings.objects.first()
        if settings_obj and settings_obj.ai_api_key:
            return {
                'api_key': settings_obj.ai_api_key,
                'base_url': settings_obj.ai_base_url or 'https://openrouter.ai/api/v1',
                'model': settings_obj.ai_model or 'deepseek/deepseek-r1-0528:free',
            }
    except Exception:
        pass

    return {
        'api_key': os.environ.get('AI_API_KEY', ''),
        'base_url': os.environ.get('AI_BASE_URL', 'https://openrouter.ai/api/v1'),
        'model': os.environ.get('AI_MODEL', 'deepseek/deepseek-r1-0528:free'),
    }


BATCH_SIZE = 15
BATCH_DELAY = 3


def generate_exam_questions(topic, subject, num_questions=None, question_types=None, difficulty='medium', type_counts=None):
    """
    Generate exam questions using the OpenRouter API in batches to avoid timeouts.

    Args:
        topic: The topic(s) to generate questions about (comma-separated)
        subject: The subject area (e.g., Science, Math, English)
        num_questions: Total number of questions (legacy, used if type_counts not provided)
        question_types: List of question types (legacy, used if type_counts not provided)
        difficulty: easy, medium, or hard
        type_counts: Dict of {question_type: count} for per-type generation

    Returns:
        List of question dictionaries ready to be saved
    """
    config = get_ai_config()
    api_key = config['api_key']
    base_url = config['base_url']
    model = config['model']

    if not api_key:
        raise ValueError(
            'AI API key is not configured. '
            'Set it in Superadmin > AI Settings or in the .env file (AI_API_KEY).'
        )

    # Build batches from type_counts or legacy params
    if type_counts:
        batches = _build_batches_from_counts(type_counts)
    else:
        total_questions = num_questions or 10
        question_types = question_types or ['MCQ', 'TRUE_FALSE']
        per_type = total_questions // len(question_types)
        remainder = total_questions % len(question_types)
        type_counts = {}
        for i, qt in enumerate(question_types):
            type_counts[qt] = per_type + (1 if i < remainder else 0)
        batches = _build_batches_from_counts(type_counts)

    all_questions = []
    for i, batch in enumerate(batches):
        if i > 0:
            time.sleep(BATCH_DELAY)

        batch_questions = _generate_batch(batch, topic, subject, difficulty, api_key, base_url, model)
        all_questions.extend(batch_questions)

    return all_questions


def _build_batches_from_counts(type_counts):
    """Split type_counts into batches of BATCH_SIZE questions max."""
    items = []
    for qt, count in type_counts.items():
        if count > 0 and qt in QUESTION_TYPE_CONFIGS:
            items.append((qt, count))

    batches = []
    current_batch = {}
    current_size = 0

    for qt, count in items:
        remaining = count
        while remaining > 0:
            space = BATCH_SIZE - current_size
            take = min(remaining, space)
            current_batch[qt] = current_batch.get(qt, 0) + take
            current_size += take
            remaining -= take

            if current_size >= BATCH_SIZE:
                batches.append(current_batch)
                current_batch = {}
                current_size = 0

    if current_batch:
        batches.append(current_batch)

    return batches


def _generate_batch(batch_counts, topic, subject, difficulty, api_key, base_url, model):
    """Generate a single batch of questions."""
    batch_total = sum(batch_counts.values())

    type_instructions = []
    for qt, count in batch_counts.items():
        config_qt = QUESTION_TYPE_CONFIGS[qt]
        type_instructions.append(f"- {qt} ({count} questions): {config_qt['description']}\n  Format: {config_qt['format']}")

    types_text = '\n'.join(type_instructions)

    prompt = f"""You are an expert exam creator for educational institutions. Generate exactly {batch_total} exam questions about the following:

Subject: {subject}
Topics: {topic}
Difficulty: {difficulty}

Question types and counts to generate:
{types_text}

RULES:
1. Questions must be clear, unambiguous, and appropriate for students
2. Distribute questions evenly across all listed topics
3. Generate EXACTLY the specified number of questions for each type
4. For MCQ: Always provide exactly 4 options (A, B, C, D). Only ONE correct answer.
5. For TRUE_FALSE: The correct_answer must be a boolean (true or false)
6. For IDENTIFICATION: Provide 1-3 acceptable answers as an array
7. For ENUMERATION: List all correct items and set min_required appropriately
8. For ESSAY: Set correct_answer to null
9. Questions should test understanding, not just memorization
10. Vary the difficulty based on the specified level
11. Make distractors (wrong options) plausible but clearly incorrect to someone who studied

Return ONLY a valid JSON array of question objects. No markdown, no explanation, just the JSON array."""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://seamless-exam.com',
        'X-Title': 'Seamless Exam System',
    }

    payload = {
        'model': model,
        'messages': [
            {
                'role': 'system',
                'content': 'You are an expert exam question generator. You output only valid JSON arrays. No markdown formatting, no code blocks, just raw JSON.'
            },
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'temperature': 0.7,
        'max_tokens': 4096,
    }

    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        data = response.json()
        content = data['choices'][0]['message']['content'].strip()

        # Clean up response - remove markdown code blocks if present
        if content.startswith('```'):
            content = content.split('\n', 1)[1] if '\n' in content else content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

        if content.startswith('json'):
            content = content[4:].strip()

        questions = json.loads(content)

        if not isinstance(questions, list):
            raise ValueError('AI response is not a list of questions')

        validated = []
        for q in questions:
            validated_q = _validate_and_normalize(q)
            if validated_q:
                validated.append(validated_q)

        return validated

    except requests.exceptions.Timeout:
        raise ValueError('AI service timed out. Please try again.')
    except requests.exceptions.HTTPError as e:
        logger.error(f'OpenRouter API error: {e.response.status_code} - {e.response.text}')
        raise ValueError(f'AI service error: {e.response.status_code}')
    except json.JSONDecodeError:
        logger.error(f'Failed to parse AI response: {content[:500]}')
        raise ValueError('AI returned invalid format. Please try again.')
    except (KeyError, IndexError) as e:
        logger.error(f'Unexpected AI response structure: {e}')
        raise ValueError('Unexpected AI response. Please try again.')


def _validate_and_normalize(question):
    """Validate and normalize a question dict to match the database schema."""
    if not isinstance(question, dict):
        return None

    q_type = question.get('type', '').upper()
    q_text = question.get('question', '').strip()
    points = question.get('points', 1.0)

    if not q_text or q_type not in QUESTION_TYPE_CONFIGS:
        return None

    try:
        points = float(points)
        if points <= 0:
            points = 1.0
    except (ValueError, TypeError):
        points = 1.0

    result = {
        'question_type': q_type,
        'question_text': q_text,
        'points': points,
        'options': [],
        'correct_answer': None,
    }

    if q_type == 'MCQ':
        options = question.get('options', [])
        if not options or len(options) < 2:
            return None
        normalized_options = []
        for i, opt in enumerate(options[:4]):
            key = opt.get('key', chr(ord('A') + i))
            value = opt.get('value', '').strip()
            if not value:
                return None
            normalized_options.append({'key': key, 'value': value})
        result['options'] = normalized_options
        result['correct_answer'] = question.get('correct_answer', 'A')

    elif q_type == 'TRUE_FALSE':
        answer = question.get('correct_answer')
        if isinstance(answer, str):
            answer = answer.lower() == 'true'
        result['correct_answer'] = bool(answer)

    elif q_type == 'IDENTIFICATION':
        answer = question.get('correct_answer', [])
        if isinstance(answer, str):
            answer = [answer]
        if not answer:
            return None
        result['correct_answer'] = answer

    elif q_type == 'ENUMERATION':
        answer = question.get('correct_answer', {})
        if isinstance(answer, dict):
            items = answer.get('items', [])
            min_req = answer.get('min_required', len(items))
            result['correct_answer'] = {'items': items, 'min_required': min_req}
        elif isinstance(answer, list):
            result['correct_answer'] = {'items': answer, 'min_required': len(answer)}
        else:
            return None

    elif q_type == 'ESSAY':
        result['correct_answer'] = None

    return result
