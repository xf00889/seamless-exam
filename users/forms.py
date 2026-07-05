from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator


class TeacherLoginForm(forms.Form):
    username = forms.CharField(
        max_length=150, required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Username', 'autocomplete': 'username',
        }),
        error_messages={'required': 'Username is required'},
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password', 'autocomplete': 'current-password',
        }),
        error_messages={'required': 'Password is required'},
    )


class StudentLoginForm(forms.Form):
    student_id = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'School ID', 'autocomplete': 'username',
        }),
        error_messages={'required': 'School ID is required'},
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password', 'autocomplete': 'current-password',
        }),
        error_messages={'required': 'Password is required'},
    )


class ProfileEditForm(forms.Form):
    first_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'First Name',
        }),
    )
    last_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Last Name',
        }),
    )
    bio = forms.CharField(
        max_length=500, required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Tell us about yourself (optional)', 'rows': 4,
        }),
    )

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise ValidationError('First name cannot be empty')
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise ValidationError('Last name cannot be empty')
        return last_name


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Current Password', 'autocomplete': 'current-password',
        }),
    )
    new_password = forms.CharField(
        required=True,
        validators=[MinLengthValidator(8, 'Password must be at least 8 characters long')],
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'New Password', 'autocomplete': 'new-password',
        }),
    )
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Confirm New Password', 'autocomplete': 'new-password',
        }),
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')
        if not password:
            raise ValidationError('New password cannot be empty')
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain at least one digit')
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            raise ValidationError('New password and confirmation do not match')
        return cleaned_data


class ProfilePictureForm(forms.Form):
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
            'accept': 'image/jpeg,image/jpg,image/png,image/gif',
        }),
    )

    def clean_profile_picture(self):
        picture = self.cleaned_data.get('profile_picture')
        if not picture:
            raise ValidationError('Please select an image file')
        max_size = 5 * 1024 * 1024
        if picture.size > max_size:
            raise ValidationError(f'File size exceeds maximum allowed size (5MB)')
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if picture.content_type not in allowed_types:
            raise ValidationError('Please upload a JPEG, PNG, or GIF image.')
        return picture


class ClassForm(forms.Form):
    grade_level = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
        error_messages={'required': 'Grade level is required'},
    )
    strand = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
        error_messages={'required': 'Strand is required'},
    )
    section = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
        error_messages={'required': 'Section is required'},
    )

    def __init__(self, *args, school_id=None, class_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.school_id = school_id
        self.class_id = class_id
        from users.models import GradeLevel, Strand, Section
        gl_qs = GradeLevel.objects.filter(school_id=school_id) if school_id else GradeLevel.objects.none()
        strand_qs = Strand.objects.filter(school_id=school_id) if school_id else Strand.objects.none()
        sec_qs = Section.objects.filter(school_id=school_id) if school_id else Section.objects.none()
        self.fields['grade_level'].choices = [('', '-- Select Grade Level --')] + [
            (str(gl.id), gl.name) for gl in gl_qs
        ]
        self.fields['strand'].choices = [('', '-- Select Strand --')] + [
            (str(s.id), s.name) for s in strand_qs
        ]
        self.fields['section'].choices = [('', '-- Select Section --')] + [
            (str(s.id), s.name) for s in sec_qs
        ]

    def clean_grade_level(self):
        val = self.cleaned_data.get('grade_level', '').strip()
        if not val:
            raise ValidationError('Grade level cannot be empty')
        return int(val)

    def clean_strand(self):
        val = self.cleaned_data.get('strand', '').strip()
        if not val:
            raise ValidationError('Strand cannot be empty')
        return int(val)

    def clean_section(self):
        val = self.cleaned_data.get('section', '').strip()
        if not val:
            raise ValidationError('Section cannot be empty')
        return int(val)

    def clean(self):
        cleaned_data = super().clean()
        grade_level_id = cleaned_data.get('grade_level')
        strand_id = cleaned_data.get('strand')
        section_id = cleaned_data.get('section')
        if grade_level_id and strand_id and section_id and self.school_id:
            from repositories.class_repository import ClassRepository
            repo = ClassRepository()
            if repo.check_duplicate_class(
                school_id=self.school_id,
                grade_level_id=grade_level_id,
                strand_id=strand_id,
                section_id=section_id,
                exclude_id=self.class_id,
            ):
                raise ValidationError('A class with these details already exists in this school')
        return cleaned_data


class StudentClassAssignmentForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=None, required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
    )
    class_assigned = forms.ModelChoiceField(
        queryset=None, required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
    )

    def __init__(self, *args, school_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import Student, Class
        if school_id:
            self.fields['student'].queryset = Student.objects.filter(
                school_id=school_id
            ).order_by('last_name', 'first_name')
            self.fields['class_assigned'].queryset = Class.objects.filter(
                school_id=school_id
            ).order_by('grade_level__name', 'strand__name', 'section__name')
        else:
            self.fields['student'].queryset = Student.objects.none()
            self.fields['class_assigned'].queryset = Class.objects.none()


class BulkStudentAssignmentForm(forms.Form):
    students = forms.ModelMultipleChoiceField(
        queryset=None, required=True,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded',
        }),
    )
    class_assigned = forms.ModelChoiceField(
        queryset=None, required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
    )

    def __init__(self, *args, school_id=None, initial_class_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import Student, Class
        if school_id:
            students_qs = Student.objects.filter(
                school_id=school_id
            ).order_by('last_name', 'first_name')
            if initial_class_id:
                students_qs = students_qs.exclude(class_assigned_id=initial_class_id)
            self.fields['students'].queryset = students_qs
            self.fields['class_assigned'].queryset = Class.objects.filter(
                school_id=school_id
            ).order_by('grade_level__name', 'strand__name', 'section__name')
            if initial_class_id and not self.data:
                try:
                    selected = Class.objects.get(id=initial_class_id, school_id=school_id)
                    self.fields['class_assigned'].initial = selected
                    self.fields['class_assigned'].widget.attrs['data-preselected'] = 'true'
                except Class.DoesNotExist:
                    pass
        else:
            self.fields['students'].queryset = Student.objects.none()
            self.fields['class_assigned'].queryset = Class.objects.none()


class StudentCreationForm(forms.Form):
    student_id = forms.CharField(
        max_length=50, required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'e.g., 2024-0001',
        }),
    )
    first_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'First Name',
        }),
    )
    last_name = forms.CharField(
        max_length=100, required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Last Name',
        }),
    )
    class_assigned = forms.ModelChoiceField(
        queryset=None, required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        }),
    )

    def __init__(self, *args, school_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        from users.models import Class
        if school_id:
            self.fields['class_assigned'].queryset = Class.objects.filter(
                school_id=school_id
            ).order_by('grade_level__name', 'strand__name', 'section__name')
        else:
            self.fields['class_assigned'].queryset = Class.objects.none()

    def clean_student_id(self):
        from users.models import Student
        val = self.cleaned_data.get('student_id', '').strip()
        if not val:
            raise ValidationError('Student ID cannot be empty')
        if Student.objects.filter(student_id=val).exists():
            raise ValidationError(f'A student with ID "{val}" already exists')
        return val

    def clean_first_name(self):
        val = self.cleaned_data.get('first_name', '').strip()
        if not val:
            raise ValidationError('First name cannot be empty')
        return val

    def clean_last_name(self):
        val = self.cleaned_data.get('last_name', '').strip()
        if not val:
            raise ValidationError('Last name cannot be empty')
        return val

    @staticmethod
    def generate_password(student_id, last_name):
        digits = ''.join(filter(str.isdigit, student_id))[:4]
        if len(digits) < 4:
            digits = digits.ljust(4, '0')
        letters = ''.join(filter(str.isalpha, last_name))[:4].upper()
        if len(letters) < 4:
            letters = letters.ljust(4, 'X')
        return digits + letters
