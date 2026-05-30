"""
Django forms for exam management.
Provides server-side validation for exam and question creation/editing.
Requirements: 1.2, 2.2
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from exams.models import Exam, Question, QuestionType
from users.models import Class
import json


class ExamForm(forms.ModelForm):
    """
    Form for creating and editing exams.
    Validates exam title, subject, description, duration, and file uploads.
    Supports three creation methods: AI generation, file upload, and manual entry.
    Requirements: 1.1, 1.2, 1.3, 1.4
    """
    
    # Generation method choice field (Requirement 1.1)
    GENERATION_METHOD_CHOICES = [
        ('manual', 'Manual Entry'),
        ('ai_generate', 'AI Generate'),
    ]
    
    generation_method = forms.ChoiceField(
        choices=GENERATION_METHOD_CHOICES,
        required=True,
        initial='manual',
        widget=forms.RadioSelect(attrs={
            'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300',
        }),
        help_text='Choose how you want to create exam questions'
    )
    
    # AI generation fields (Requirement 1.2)
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('MCQ', 'Multiple Choice'),
        ('IDENTIFICATION', 'Identification'),
        ('ENUMERATION', 'Enumeration'),
        ('TRUE_FALSE', 'True/False'),
        ('ESSAY', 'Essay'),
    ]
    
    ai_topic = forms.CharField(
        max_length=1000,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'e.g., Photosynthesis, Cell Division, Respiration\nor\nWorld War II, Cold War, Industrial Revolution',
            'rows': '3',
            'data-field-name': 'Topics',
        }),
        help_text='Enter one or more topics (separate multiple topics with commas or new lines)'
    )
    
    ai_subject = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': 'e.g., Biology, History, Mathematics',
            'data-field-name': 'Subject',
        }),
        help_text='Subject area for the questions'
    )
    
    ai_difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'data-field-name': 'Difficulty',
        }),
        help_text='Difficulty level for generated questions'
    )
    
    ai_num_questions = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'placeholder': '10',
            'min': '1',
            'max': '100',
            'data-field-name': 'Number of Questions',
        }),
        help_text='Number of questions to generate (1-100)'
    )
    
    ai_question_types = forms.MultipleChoiceField(
        choices=QUESTION_TYPE_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded',
        }),
        help_text='Select one or more question types to generate'
    )
    
    # Class assignment field (Requirement 3.1)
    assigned_classes = forms.ModelMultipleChoiceField(
        queryset=Class.objects.none(),  # Will be set in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded',
        }),
        help_text='Select classes that can access this exam (optional)'
    )
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            for field_name in ['generation_method', 'ai_topic', 'ai_subject', 'ai_num_questions', 'ai_difficulty', 'ai_question_types']:
                if field_name in self.fields:
                    del self.fields[field_name]

        # Populate subject dropdown from lookup table
        from users.models import Subject
        subject_choices = [('', '-- Select Subject --')] + [
            (s.name, s.name) for s in Subject.objects.all()
        ]
        self.fields['subject'].widget = forms.Select(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
            'data-field-name': 'Subject',
        })
        self.fields['subject'].widget.choices = subject_choices

        # Set queryset for assigned_classes based on teacher
        if teacher:
            self.fields['assigned_classes'].queryset = Class.objects.filter(
                teacher=teacher
            ).order_by('grade_level', 'strand', 'section')
    
    class Meta:
        model = Exam
        fields = ['title', 'subject', 'description', 'duration_minutes']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Enter exam title',
                'maxlength': '255',
                'data-field-name': 'Title'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'e.g., English, Physical Science, Filipino',
                'maxlength': '100',
                'data-field-name': 'Subject'
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Enter exam description (optional)',
                'rows': '3',
                'data-field-name': 'Description'
            }),
            'duration_minutes': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Duration in minutes',
                'min': '1',
                'max': '480',
                'data-field-name': 'Duration'
            }),
        }
        error_messages = {
            'title': {
                'required': 'Exam title is required',
                'max_length': 'Title must not exceed 255 characters'
            },
            'subject': {
                'max_length': 'Subject must not exceed 100 characters'
            },
            'duration_minutes': {
                'required': 'Duration is required',
                'invalid': 'Please enter a valid number'
            }
        }
    
    def clean_title(self):
        """Validate and clean title field."""
        title = self.cleaned_data.get('title', '').strip()
        
        if not title:
            raise ValidationError('Exam title cannot be empty')
        
        if len(title) < 3:
            raise ValidationError('Exam title must be at least 3 characters long')
        
        return title
    
    def clean_duration_minutes(self):
        """Validate and clean duration field."""
        duration = self.cleaned_data.get('duration_minutes')
        
        if duration is None:
            raise ValidationError('Duration is required')
        
        if duration <= 0:
            raise ValidationError('Duration must be a positive number')
        
        if duration > 480:  # 8 hours max
            raise ValidationError('Duration cannot exceed 480 minutes (8 hours)')
        
        return duration

    def clean_ai_topic(self):
        """Validate and clean AI topic field."""
        topic = self.cleaned_data.get('ai_topic', '').strip()
        
        if topic and len(topic) < 3:
            raise ValidationError('Topics must be at least 3 characters long')
        
        if topic and len(topic) > 1000:
            raise ValidationError('Topics must not exceed 1000 characters')
        
        # Validate that at least one topic is provided when not empty
        if topic:
            # Split by comma or newline and check each topic
            topics = [t.strip() for t in topic.replace('\n', ',').split(',') if t.strip()]
            if not topics:
                raise ValidationError('At least one valid topic is required')
            
            # Check each topic has minimum length
            for t in topics:
                if len(t) < 3:
                    raise ValidationError(f'Each topic must be at least 3 characters long: "{t}"')
        
        return topic
    
    def clean_ai_subject(self):
        """Validate and clean AI subject field."""
        subject = self.cleaned_data.get('ai_subject', '').strip()
        
        if subject and len(subject) < 2:
            raise ValidationError('Subject must be at least 2 characters long')
        
        if subject and len(subject) > 100:
            raise ValidationError('Subject must not exceed 100 characters')
        
        return subject
    
    def clean_ai_num_questions(self):
        """Validate AI number of questions field."""
        num_questions = self.cleaned_data.get('ai_num_questions')
        
        if num_questions is not None:
            if num_questions < 1:
                raise ValidationError('Number of questions must be at least 1')
            
            if num_questions > 100:
                raise ValidationError('Number of questions cannot exceed 100')
        
        return num_questions
    
    def clean(self):
        """
        Conditional validation based on generation method.
        """
        cleaned_data = super().clean()
        return cleaned_data


class QuestionForm(forms.ModelForm):
    """
    Form for creating and editing questions.
    Validates question text, type, points, and type-specific fields.
    """
    
    class Meta:
        model = Question
        fields = ['question_type', 'question_text', 'points', 'options', 'correct_answer']
        widgets = {
            'question_type': forms.Select(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'data-field-name': 'Question Type'
            }),
            'question_text': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Enter question text',
                'rows': '3',
                'data-field-name': 'Question Text'
            }),
            'points': forms.NumberInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm',
                'placeholder': 'Points',
                'min': '0.1',
                'max': '100',
                'step': '0.5',
                'data-field-name': 'Points'
            })
        }
        error_messages = {
            'question_type': {
                'required': 'Question type is required'
            },
            'question_text': {
                'required': 'Question text is required'
            },
            'points': {
                'required': 'Points are required',
                'invalid': 'Please enter a valid number'
            }
        }
    
    def clean_question_text(self):
        """Validate and clean question text field."""
        text = self.cleaned_data.get('question_text', '').strip()
        
        if not text:
            raise ValidationError('Question text cannot be empty')
        
        if len(text) < 5:
            raise ValidationError('Question text must be at least 5 characters long')
        
        return text
    
    def clean_points(self):
        """Validate and clean points field."""
        points = self.cleaned_data.get('points')
        
        if points is None:
            raise ValidationError('Points are required')
        
        if points <= 0:
            raise ValidationError('Points must be a positive number')
        
        if points > 100:
            raise ValidationError('Points cannot exceed 100')
        
        return points
    
    def clean(self):
        """Validate type-specific fields."""
        cleaned_data = super().clean()
        question_type = cleaned_data.get('question_type')
        options = cleaned_data.get('options')
        correct_answer = cleaned_data.get('correct_answer')
        
        if question_type == QuestionType.MCQ:
            # Validate MCQ options
            if not options or not isinstance(options, (list, str)):
                raise ValidationError('MCQ questions must have options')
            
            # Parse options if string
            if isinstance(options, str):
                try:
                    options = json.loads(options)
                except json.JSONDecodeError:
                    raise ValidationError('Invalid options format')
            
            if len(options) < 2:
                raise ValidationError('MCQ questions must have at least 2 options')
            
            # Validate correct answer
            if not correct_answer:
                raise ValidationError('MCQ questions must have a correct answer')
        
        elif question_type == QuestionType.IDENTIFICATION:
            # Validate identification correct answer
            if not correct_answer:
                raise ValidationError('Identification questions must have a correct answer')
        
        elif question_type == QuestionType.ENUMERATION:
            # Validate enumeration correct answers
            if not correct_answer:
                raise ValidationError('Enumeration questions must have correct answers')
        
        elif question_type == QuestionType.TRUE_FALSE:
            # Validate true/false correct answer
            if correct_answer is None:
                raise ValidationError('True/False questions must have a correct answer')
        
        return cleaned_data


class MCQOptionForm(forms.Form):
    """
    Form for MCQ option validation.
    """
    option_key = forms.CharField(
        max_length=10,
        required=True,
        error_messages={
            'required': 'Option key is required'
        }
    )
    
    option_value = forms.CharField(
        max_length=500,
        required=True,
        error_messages={
            'required': 'Option value is required'
        }
    )
    
    def clean_option_key(self):
        """Validate option key."""
        key = self.cleaned_data.get('option_key', '').strip().upper()
        
        if not key:
            raise ValidationError('Option key cannot be empty')
        
        if not key.isalpha() or len(key) != 1:
            raise ValidationError('Option key must be a single letter (A, B, C, etc.)')
        
        return key
    
    def clean_option_value(self):
        """Validate option value."""
        value = self.cleaned_data.get('option_value', '').strip()
        
        if not value:
            raise ValidationError('Option value cannot be empty')
        
        if len(value) < 1:
            raise ValidationError('Option value must not be empty')
        
        return value
