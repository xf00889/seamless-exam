import json
import logging
import math
from decimal import Decimal
from django.db.models import Count, Q, Sum, Avg, StdDev

from exams.models import Exam, Question
from attempts.models import Attempt, Answer, AttemptStatus

logger = logging.getLogger(__name__)

DIFFICULTY_LEVELS = [
    (81, 100, 'Easy'),
    (61, 80, 'Moderately Easy'),
    (41, 60, 'Average'),
    (21, 40, 'Difficult'),
    (0, 20, 'Very Difficult'),
]

ACTION_MAP = {
    'Easy': 'Retain item',
    'Moderately Easy': 'Retain item',
    'Average': 'Review item',
    'Difficult': 'Reteach competency',
    'Very Difficult': 'Revise item and reteach',
}

MASTERY_LEVELS = [
    (76, 100, 'Mastered', 'Enrichment'),
    (51, 75, 'Developing', 'Reinforcement'),
    (26, 50, 'Developing', 'Remediation'),
    (0, 25, 'Beginning', 'Intensive intervention'),
]


def get_difficulty_level(percent_correct):
    for low, high, label in DIFFICULTY_LEVELS:
        if low <= percent_correct <= high:
            return label
    return 'Very Difficult'


def get_action_needed(difficulty_level):
    return ACTION_MAP.get(difficulty_level, 'Review item')


def get_mastery_info(avg_percent):
    for low, high, level, intervention in MASTERY_LEVELS:
        if low <= avg_percent <= high:
            return level, intervention
    return 'Beginning', 'Intensive intervention'


class ItemAnalysisService:

    def get_item_summary(self, exam_id):
        """
        Compute the DepEd-style Item Summary for a given exam.
        Only considers graded attempts.
        """
        try:
            exam = Exam.objects.prefetch_related('questions').get(id=exam_id)
        except Exam.DoesNotExist:
            return None

        questions = exam.questions.all().order_by('order_index', 'id')
        graded_attempts = Attempt.objects.filter(
            exam=exam,
            status=AttemptStatus.GRADED
        )
        total_learners = graded_attempts.count()

        if total_learners == 0:
            return {
                'exam': exam,
                'total_learners': 0,
                'items': [],
                'competency_summary': [],
                'overall_stats': {},
                'difficulty_distribution': {},
                'has_data': False,
            }

        attempt_ids = list(graded_attempts.values_list('id', flat=True))

        total_possible = float(sum(q.points for q in questions))

        items = []
        for idx, question in enumerate(questions, start=1):
            answers = Answer.objects.filter(
                attempt_id__in=attempt_ids,
                question=question
            )
            total_answered = answers.count()
            num_correct = answers.filter(is_correct=True).count()
            num_wrong = answers.filter(is_correct=False).count()
            num_skipped = total_learners - total_answered

            percent_correct = round((num_correct / total_learners) * 100) if total_learners > 0 else 0
            difficulty = get_difficulty_level(percent_correct)
            action = get_action_needed(difficulty)

            items.append({
                'item_no': idx,
                'question_id': question.id,
                'question_text': question.question_text,
                'question_type': question.get_question_type_display(),
                'question_type_raw': question.question_type,
                'points': float(question.points),
                'num_correct': num_correct,
                'num_wrong': num_wrong,
                'num_skipped': num_skipped,
                'total_answered': total_answered,
                'percent_correct': percent_correct,
                'difficulty_level': difficulty,
                'action_needed': action,
            })

        competency_summary = self._build_competency_summary(items)
        overall_stats = self._compute_overall_stats(graded_attempts, total_possible, total_learners)
        difficulty_distribution = self._compute_difficulty_distribution(items)
        mps_data = self._compute_mps(items, total_learners, exam, attempt_ids)

        return {
            'exam': exam,
            'total_learners': total_learners,
            'total_possible': total_possible,
            'items': items,
            'competency_summary': competency_summary,
            'overall_stats': overall_stats,
            'difficulty_distribution': difficulty_distribution,
            'mps_data': mps_data,
            'has_data': True,
        }

    def _compute_overall_stats(self, graded_attempts, total_possible, total_learners):
        """Compute overall exam statistics: average, passing rate, std deviation."""
        scores = list(graded_attempts.values_list('total_score', flat=True))
        float_scores = [float(s) for s in scores]

        if not float_scores:
            return {}

        avg_score = sum(float_scores) / len(float_scores)
        avg_percent = (avg_score / total_possible * 100) if total_possible > 0 else 0

        passing_count = sum(1 for s in float_scores if (s / total_possible * 100) >= 60) if total_possible > 0 else 0
        passing_rate = (passing_count / total_learners * 100) if total_learners > 0 else 0

        if len(float_scores) > 1:
            mean = avg_score
            variance = sum((x - mean) ** 2 for x in float_scores) / (len(float_scores) - 1)
            std_dev = math.sqrt(variance)
        else:
            std_dev = 0

        highest = max(float_scores)
        lowest = min(float_scores)

        return {
            'avg_score': round(avg_score, 2),
            'avg_percent': round(avg_percent, 1),
            'passing_count': passing_count,
            'failing_count': total_learners - passing_count,
            'passing_rate': round(passing_rate, 1),
            'std_dev': round(std_dev, 2),
            'highest_score': round(highest, 2),
            'lowest_score': round(lowest, 2),
            'total_possible': round(total_possible, 2),
        }

    def _compute_difficulty_distribution(self, items):
        """Count items per difficulty level."""
        dist = {
            'Easy': 0,
            'Moderately Easy': 0,
            'Average': 0,
            'Difficult': 0,
            'Very Difficult': 0,
        }
        for item in items:
            level = item['difficulty_level']
            if level in dist:
                dist[level] += 1
        total = len(items)
        dist_with_percent = {}
        for level, count in dist.items():
            dist_with_percent[level] = {
                'count': count,
                'percent': round((count / total) * 100) if total > 0 else 0,
            }
        return dist_with_percent

    def _compute_mps(self, items, total_learners, exam, attempt_ids):
        """
        Compute Mean Percentage Score (MPS).
        MPS = (Total Correct Answers / Total Possible Answers) × 100
        Also computes per-class breakdown.
        """
        from users.models import Class
        from exams.models import ExamClassAssignment

        total_items = len(items)
        total_correct = sum(item['num_correct'] for item in items)
        total_possible_answers = total_learners * total_items

        overall_mps = round((total_correct / total_possible_answers) * 100, 2) if total_possible_answers > 0 else 0

        per_class = []
        assigned_classes = Class.objects.filter(
            exam_assignments__exam=exam
        ).order_by('grade_level', 'strand', 'section')

        for cls in assigned_classes:
            class_attempts = Attempt.objects.filter(
                id__in=attempt_ids,
                student__class_assigned=cls
            )
            class_learners = class_attempts.count()
            if class_learners == 0:
                continue

            class_attempt_ids = list(class_attempts.values_list('id', flat=True))
            class_correct = 0
            for item in items:
                correct_count = Answer.objects.filter(
                    attempt_id__in=class_attempt_ids,
                    question_id=item['question_id'],
                    is_correct=True
                ).count()
                class_correct += correct_count

            class_possible = class_learners * total_items
            class_mps = round((class_correct / class_possible) * 100, 2) if class_possible > 0 else 0

            per_class.append({
                'class_name': str(cls),
                'grade_level': cls.grade_level,
                'strand': cls.strand,
                'section': cls.section,
                'learners': class_learners,
                'total_correct': class_correct,
                'total_possible': class_possible,
                'mps': class_mps,
            })

        return {
            'overall_mps': overall_mps,
            'total_correct': total_correct,
            'total_possible_answers': total_possible_answers,
            'total_items': total_items,
            'total_learners': total_learners,
            'per_class': per_class,
        }

    def _build_competency_summary(self, items):
        """
        Group items by question type and compute mastery levels.
        Since questions don't have explicit MELC/competency fields,
        we group by question type as a proxy.
        """
        type_groups = {}
        for item in items:
            qt = item['question_type']
            if qt not in type_groups:
                type_groups[qt] = {
                    'competency': qt,
                    'items': [],
                    'percents': [],
                }
            type_groups[qt]['items'].append(item['item_no'])
            type_groups[qt]['percents'].append(item['percent_correct'])

        summary = []
        for qt, data in type_groups.items():
            avg_percent = round(sum(data['percents']) / len(data['percents'])) if data['percents'] else 0
            mastery_level, intervention = get_mastery_info(avg_percent)

            item_range = f"{data['items'][0]}"
            if len(data['items']) > 1:
                item_range = f"{data['items'][0]}-{data['items'][-1]}"

            summary.append({
                'competency': data['competency'],
                'items': ', '.join(str(i) for i in data['items']),
                'item_range': item_range,
                'avg_percent': avg_percent,
                'mastery_level': mastery_level,
                'intervention': intervention,
            })

        return summary

    def get_ai_analysis_prompt(self, summary_data):
        """
        Build a prompt for AI-powered teacher analysis based on item summary data.
        """
        if not summary_data or not summary_data.get('has_data'):
            return None

        exam = summary_data['exam']
        items = summary_data['items']
        total_learners = summary_data['total_learners']

        easy_items = [i for i in items if i['difficulty_level'] == 'Easy']
        moderate_items = [i for i in items if i['difficulty_level'] == 'Moderately Easy']
        average_items = [i for i in items if i['difficulty_level'] == 'Average']
        difficult_items = [i for i in items if i['difficulty_level'] == 'Difficult']
        very_difficult_items = [i for i in items if i['difficulty_level'] == 'Very Difficult']

        items_detail = ""
        for item in items:
            items_detail += (
                f"Item {item['item_no']}: {item['question_text'][:80]} | "
                f"Type: {item['question_type']} | "
                f"Correct: {item['num_correct']}/{total_learners} ({item['percent_correct']}%) | "
                f"Skipped: {item['num_skipped']} | "
                f"Difficulty: {item['difficulty_level']}\n"
            )

        overall = summary_data.get('overall_stats', {})
        overall_text = ""
        if overall:
            overall_text = f"""
OVERALL STATISTICS:
- Average Score: {overall.get('avg_score', 0)}/{overall.get('total_possible', 0)} ({overall.get('avg_percent', 0)}%)
- Passing Rate (60%): {overall.get('passing_rate', 0)}% ({overall.get('passing_count', 0)} passed, {overall.get('failing_count', 0)} failed)
- Standard Deviation: {overall.get('std_dev', 0)}
- Highest Score: {overall.get('highest_score', 0)}
- Lowest Score: {overall.get('lowest_score', 0)}
"""

        prompt = f"""You are an expert DepEd (Department of Education, Philippines) assessment specialist.
Analyze the following Item Summary data from a summative/quarterly assessment and provide a Teacher's Analysis report.

EXAM: {exam.title}
SUBJECT: {exam.subject or 'Not specified'}
TOTAL LEARNERS: {total_learners}
TOTAL ITEMS: {len(items)}
{overall_text}
DIFFICULTY DISTRIBUTION:
- Easy (81-100%): {len(easy_items)} items
- Moderately Easy (61-80%): {len(moderate_items)} items
- Average (41-60%): {len(average_items)} items
- Difficult (21-40%): {len(difficult_items)} items
- Very Difficult (0-20%): {len(very_difficult_items)} items

ITEM DETAILS:
{items_detail}

Based on this data, provide a structured Teacher's Analysis in the following JSON format:
{{
    "strengths": ["list of 2-3 specific strengths based on the data"],
    "areas_for_improvement": ["list of 2-3 specific areas where learners struggled"],
    "intervention_plan": ["list of 3-4 specific, actionable intervention steps"],
    "items_to_revise": ["list of item numbers that may need revision due to very low performance or possible poor construction"],
    "overall_assessment": "A 2-3 sentence overall assessment of the test results"
}}

RULES:
1. Base your analysis ONLY on the data provided
2. Be specific - reference actual item numbers and percentages
3. Intervention steps should be practical and aligned with DepEd practices
4. Consider whether very difficult items indicate poor instruction OR poor item construction
5. Items with high skip rates may indicate time pressure rather than difficulty
6. Return ONLY valid JSON, no markdown or explanation"""

        return prompt

    def generate_ai_analysis(self, summary_data):
        """
        Call the AI service to generate teacher analysis.
        Returns parsed analysis dict or None on failure.
        """
        from services.ai_generation_service import get_ai_config
        import requests

        prompt = self.get_ai_analysis_prompt(summary_data)
        if not prompt:
            return None

        config = get_ai_config()
        api_key = config['api_key']
        base_url = config['base_url']
        model = config['model']

        if not api_key:
            return None

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
                    'content': 'You are a DepEd assessment specialist. Output only valid JSON. No markdown, no code blocks.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.4,
            'max_tokens': 2048,
        }

        try:
            response = requests.post(
                f'{base_url}/chat/completions',
                headers=headers,
                json=payload,
                timeout=45
            )
            response.raise_for_status()

            data = response.json()
            content = data['choices'][0]['message']['content'].strip()

            if content.startswith('```'):
                content = content.split('\n', 1)[1] if '\n' in content else content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
            if content.startswith('json'):
                content = content[4:].strip()

            analysis = json.loads(content)
            return analysis

        except requests.exceptions.Timeout:
            logger.warning('AI analysis timed out')
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f'AI analysis API error: {e.response.status_code}')
            return None
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.error(f'Failed to parse AI analysis response: {e}')
            return None
        except Exception as e:
            logger.error(f'Unexpected error in AI analysis: {e}')
            return None
