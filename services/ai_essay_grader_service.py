import json
import logging
import requests

logger = logging.getLogger(__name__)


def _extract_answer_text(answer_text):
    if isinstance(answer_text, dict):
        return (
            answer_text.get('value')
            or answer_text.get('answer')
            or answer_text.get('text')
            or ''
        )
    if isinstance(answer_text, str):
        return answer_text
    return ''


def build_essay_grader_prompt(*, question_text, answer_text, max_points, exam_title='', subject='', grade_level=''):
    """
    Build a lenient-grading prompt for an essay answer.
    Returns the prompt string (or '' if missing required inputs).
    """
    if not question_text or not answer_text or not answer_text.strip():
        return ''

    max_points_str = f'{float(max_points):.2f}'.rstrip('0').rstrip('.') or '0'

    context_lines = []
    if exam_title:
        context_lines.append(f'- Exam: {exam_title}')
    if subject:
        context_lines.append(f'- Subject: {subject}')
    if grade_level:
        context_lines.append(f'- Grade Level: {grade_level}')
    context_block = '\n'.join(context_lines) if context_lines else '- (not specified)'

    return f"""You are a DepEd teacher grading a student's essay answer.
Be LENIENT and FAIR. Reward on-topic effort and partial understanding.

EXAM CONTEXT:
{context_block}

QUESTION (worth {max_points_str} points):
{question_text}

STUDENT'S ANSWER:
\"\"\"
{answer_text.strip()}
\"\"\"

GRADING CRITERIA (LENIENT — give credit generously):
1. RELEVANCE (40%): Does the answer address the question? Off-topic = 0 points.
2. CORRECTNESS (40%): Are the facts/concepts accurate? Partial credit for partial understanding.
3. DEPTH OF THOUGHT (20%): Reasoning, examples, or analysis shown?

RULES:
- BLANK, empty, or whitespace-only answer -> 0 points (set is_blank: true).
- CLEARLY OFF-TOPIC (does not address the question at all) -> 0 points (set is_off_topic: true).
- Be LENIENT: do NOT penalize minor grammar, spelling, or punctuation issues.
- Be FAIR: give partial credit (in 0.5 increments) for partial understanding.
- Any on-topic content with some accuracy -> at least 1 point (when max_points >= 2).
- Points must be between 0 and {max_points_str}.

OUTPUT FORMAT (return ONLY valid JSON, no markdown, no code blocks):
{{
  "points_earned": <float 0 to {max_points_str}>,
  "feedback": "<constructive 1-3 sentence feedback for the student, plain text>",
  "reasoning": "<one short sentence explaining the score>",
  "is_blank": <true|false>,
  "is_off_topic": <true|false>,
  "breakdown": {{
    "relevance": <0 to 10>,
    "correctness": <0 to 10>,
    "depth": <0 to 10>
  }}
}}"""


def _parse_ai_response(content, max_points):
    if not content:
        return None
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[1] if '\n' in content else content[3:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
    if content.startswith('json'):
        content = content[4:].strip()
    return json.loads(content)


def _normalize_score(raw_points, max_points):
    try:
        points = float(raw_points)
    except (TypeError, ValueError):
        return 0.0
    if points < 0:
        return 0.0
    if points > float(max_points):
        return float(max_points)
    return round(points, 2)


def _is_blank(answer_text):
    return not answer_text or not answer_text.strip()


def grade_essay_with_ai(*, question_text, answer_text, max_points, exam_title='', subject='', grade_level=''):
    """
    Call the AI service to suggest a grade for a single essay answer.
    Returns dict {points_earned, feedback, reasoning, is_blank, is_off_topic, breakdown, model_used}
    or {'error': ..., 'code': ...} on failure.

    Local-blank short-circuit: returns 0 immediately without calling the AI
    when the answer text is empty/whitespace (the prompt would say 0 anyway).
    """
    from services.ai_generation_service import get_ai_config

    max_points_f = float(max_points)
    if max_points_f <= 0:
        return {'error': 'Question has no points configured.', 'code': 'no_points'}

    answer_str = _extract_answer_text(answer_text)

    if _is_blank(answer_str):
        return {
            'points_earned': 0,
            'feedback': 'No answer was provided.',
            'reasoning': 'Blank answer.',
            'is_blank': True,
            'is_off_topic': False,
            'breakdown': {'relevance': 0, 'correctness': 0, 'depth': 0},
            'model_used': '',
        }

    if not question_text or not str(question_text).strip():
        return {'error': 'Question has no text.', 'code': 'no_question_text'}

    prompt = build_essay_grader_prompt(
        question_text=question_text,
        answer_text=answer_str,
        max_points=max_points_f,
        exam_title=exam_title,
        subject=subject,
        grade_level=grade_level,
    )
    if not prompt:
        return {'error': 'Could not build AI prompt.', 'code': 'prompt_build_failed'}

    try:
        config = get_ai_config()
        api_key = config['api_key']
        base_url = config['base_url']
        model = config['model']
    except Exception as e:
        logger.error(f'AI essay grader: failed to load config: {e}')
        return {'error': 'AI service is not configured.', 'code': 'no_config'}

    if not api_key:
        return {
            'error': 'AI service is not configured. Ask the superadmin to set the API key in AI Settings.',
            'code': 'no_api_key',
        }

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
                'content': 'You are a DepEd teacher grading a student essay. Be lenient and fair. Output only valid JSON, no markdown, no code blocks.',
            },
            {'role': 'user', 'content': prompt},
        ],
        'temperature': 0.3,
        'max_tokens': 1024,
    }

    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers=headers,
            json=payload,
            timeout=45,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.warning('AI essay grading timed out')
        return {'error': 'AI grading timed out. Try again.', 'code': 'timeout'}
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, 'status_code', None)
        logger.error(f'AI essay grading API error: {status}')
        if status == 401:
            return {'error': 'AI API key is invalid. Ask the superadmin to check AI Settings.', 'code': 'auth_failed'}
        if status == 429:
            return {'error': 'AI service is busy. Try again in a moment.', 'code': 'rate_limited'}
        return {'error': f'AI service error (HTTP {status}). Try again.', 'code': 'http_error'}
    except requests.exceptions.RequestException as e:
        logger.error(f'AI essay grading request failed: {e}')
        return {'error': 'Cannot reach AI service. Check your network.', 'code': 'network'}

    try:
        data = response.json()
        content = data['choices'][0]['message']['content']
    except (ValueError, KeyError, IndexError) as e:
        logger.error(f'AI essay grading: unexpected response shape: {e}')
        return {'error': 'AI returned an unexpected response.', 'code': 'bad_response'}

    try:
        parsed = _parse_ai_response(content, max_points_f)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f'AI essay grading: JSON parse failed: {e}')
        return {'error': 'AI returned an invalid response. Try again.', 'code': 'parse_failed'}

    if not isinstance(parsed, dict):
        return {'error': 'AI returned an unexpected response.', 'code': 'bad_response_shape'}

    points = _normalize_score(parsed.get('points_earned', 0), max_points_f)
    feedback = str(parsed.get('feedback', '') or '').strip()[:2000]
    reasoning = str(parsed.get('reasoning', '') or '').strip()[:500]
    is_blank = bool(parsed.get('is_blank', False))
    is_off_topic = bool(parsed.get('is_off_topic', False))
    breakdown = parsed.get('breakdown') or {}
    if not isinstance(breakdown, dict):
        breakdown = {}

    return {
        'points_earned': points,
        'feedback': feedback,
        'reasoning': reasoning,
        'is_blank': is_blank,
        'is_off_topic': is_off_topic,
        'breakdown': {
            'relevance': int(breakdown.get('relevance', 0) or 0),
            'correctness': int(breakdown.get('correctness', 0) or 0),
            'depth': int(breakdown.get('depth', 0) or 0),
        },
        'model_used': model,
    }
