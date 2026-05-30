"""
Django forms for user authentication.
Provides server-side validation for teacher and student login.
Requirements: 1.2, 2.2
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator


class TeacherLoginForm(forms.Form):
    """
    Form for teacher authentication.
    Validates username and password fields.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Username',
            'autocomplete': 'username',
            'data-field-name': 'Username'
        }),
        error_messages={
            'required': 'Username is required',
            'max_length': 'Username must not exceed 150 characters'
        }
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'data-field-name': 'Password'
        }),
        error_messages={
            'required': 'Password is required'
        }
    )
    
    def clean_username(self):
        """Validate and clean username field."""
        username = self.cleaned_data.get('username', '').strip()
        
        if not username:
            raise ValidationError('Username cannot be empty')

        return username
    
    def clean_password(self):
        """Validate and clean password field."""
        password = self.cleaned_data.get('password', '')
        
        if not password:
            raise ValidationError('Password cannot be empty')

        return password


class StudentLoginForm(forms.Form):
    """
    Form for student authentication using School ID.
    Validates School ID and password fields.
    """
    school_id = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'School ID',
            'autocomplete': 'username',
            'data-field-name': 'School ID'
        }),
        error_messages={
            'required': 'School ID is required',
            'max_length': 'School ID must not exceed 50 characters'
        }
    )
    
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm',
            'placeholder': 'Password',
            'autocomplete': 'current-password',
            'data-field-name': 'Password'
        }),
        error_messages={
            'required': 'Password is required'
        }
    )
    
    def clean_school_id(self):
        """Validate and clean School ID field."""
        school_id = self.cleaned_data.get('school_id', '').strip()
        
        if not school_id:
            raise ValidationError('School ID cannot be empty')

        return school_id
    
    def clean_password(self):
        """Validate and clean password field."""
        password = self.cleaned_data.get('password', '')
        
        if not password:
            raise ValidationError('Password cannot be empty')

        return password


class ProfileEditForm(forms.Form):
    """
    Form for editing student profile information.
    Allows updating first name, last name, and bio.
    Requirements: 3.2, 3.4
    """
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'First Name',
            'data-field-name': 'First Name'
        }),
        error_messages={
            'required': 'First name is required',
            'max_length': 'First name must not exceed 100 characters'
        }
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Last Name',
            'data-field-name': 'Last Name'
        }),
        error_messages={
            'required': 'Last name is required',
            'max_length': 'Last name must not exceed 100 characters'
        }
    )
    
    bio = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Tell us about yourself (optional)',
            'rows': 4,
            'data-field-name': 'Bio'
        }),
        error_messages={
            'max_length': 'Bio must not exceed 500 characters'
        }
    )
    
    def clean_first_name(self):
        """Validate and clean first name field."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('First name cannot be empty')
        
        return first_name
    
    def clean_last_name(self):
        """Validate and clean last name field."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('Last name cannot be empty')
        
        return last_name


class PasswordChangeForm(forms.Form):
    """
    Form for changing student password.
    Requires current password and validates new password.
    Requirements: 5.2, 5.4
    """
    current_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Current Password',
            'autocomplete': 'current-password',
            'data-field-name': 'Current Password'
        }),
        error_messages={
            'required': 'Current password is required'
        }
    )
    
    new_password = forms.CharField(
        required=True,
        validators=[MinLengthValidator(8, 'Password must be at least 8 characters long')],
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'New Password',
            'autocomplete': 'new-password',
            'data-field-name': 'New Password'
        }),
        error_messages={
            'required': 'New password is required'
        }
    )
    
    confirm_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Confirm New Password',
            'autocomplete': 'new-password',
            'data-field-name': 'Confirm Password'
        }),
        error_messages={
            'required': 'Password confirmation is required'
        }
    )
    
    def clean_new_password(self):
        """Validate new password meets security requirements (Requirement 5.4)."""
        password = self.cleaned_data.get('new_password', '')
        
        if not password:
            raise ValidationError('New password cannot be empty')
        
        # Minimum 8 characters
        if len(password) < 8:
            raise ValidationError('Password must be at least 8 characters long')
        
        # At least one uppercase letter
        if not any(c.isupper() for c in password):
            raise ValidationError('Password must contain at least one uppercase letter')
        
        # At least one lowercase letter
        if not any(c.islower() for c in password):
            raise ValidationError('Password must contain at least one lowercase letter')
        
        # At least one digit
        if not any(c.isdigit() for c in password):
            raise ValidationError('Password must contain at least one digit')
        
        return password
    
    def clean(self):
        """Validate that new password and confirmation match (Requirement 5.3)."""
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError('New password and confirmation do not match')
        
        return cleaned_data


class ProfilePictureForm(forms.Form):
    """
    Form for uploading profile picture.
    Validates file type and size.
    Requirements: 4.2
    """
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100',
            'accept': 'image/jpeg,image/jpg,image/png,image/gif',
            'data-field-name': 'Profile Picture'
        }),
        error_messages={
            'required': 'Please select an image file',
            'invalid_image': 'Please upload a valid image file'
        }
    )
    
    def clean_profile_picture(self):
        """Validate profile picture file."""
        picture = self.cleaned_data.get('profile_picture')
        
        if not picture:
            raise ValidationError('Please select an image file')
        
        # File size validation (5MB max) - Requirement 4.3
        max_size = 5 * 1024 * 1024  # 5MB
        if picture.size > max_size:
            raise ValidationError(f'File size ({picture.size / (1024*1024):.2f}MB) exceeds maximum allowed size (5MB)')
        
        # File type validation - Requirement 4.2
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
        if picture.content_type not in allowed_types:
            raise ValidationError(f'File type {picture.content_type} is not allowed. Please upload a JPEG, PNG, or GIF image.')
        
        return picture


class ClassForm(forms.Form):
    """
    Form for creating and editing classes.
    Validates grade level, strand, and section fields.
    Uses dropdown selections from lookup tables.
    Requirements: 1.1, 7.1
    """
    SELECT_ATTRS = {
        'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
    }

    grade_level = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Grade Level'
        }),
        error_messages={'required': 'Grade level is required'}
    )

    strand = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Strand'
        }),
        error_messages={'required': 'Strand is required'}
    )

    section = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Section'
        }),
        error_messages={'required': 'Section is required'}
    )

    def __init__(self, *args, teacher=None, class_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.teacher = teacher
        self.class_id = class_id

        from users.models import GradeLevel, Strand, Section
        self.fields['grade_level'].choices = [('', '-- Select Grade Level --')] + [
            (gl.name, gl.name) for gl in GradeLevel.objects.all()
        ]
        self.fields['strand'].choices = [('', '-- Select Strand --')] + [
            (s.name, s.name) for s in Strand.objects.all()
        ]
        self.fields['section'].choices = [('', '-- Select Section --')] + [
            (s.name, s.name) for s in Section.objects.all()
        ]

    def clean_grade_level(self):
        grade_level = self.cleaned_data.get('grade_level', '').strip()
        if not grade_level:
            raise ValidationError('Grade level cannot be empty')
        return grade_level

    def clean_strand(self):
        strand = self.cleaned_data.get('strand', '').strip()
        if not strand:
            raise ValidationError('Strand cannot be empty')
        return strand

    def clean_section(self):
        section = self.cleaned_data.get('section', '').strip()
        if not section:
            raise ValidationError('Section cannot be empty')
        return section

    def clean(self):
        cleaned_data = super().clean()
        grade_level = cleaned_data.get('grade_level')
        strand = cleaned_data.get('strand')
        section = cleaned_data.get('section')

        if grade_level and strand and section and self.teacher:
            from repositories.class_repository import ClassRepository

            repository = ClassRepository()
            is_duplicate = repository.check_duplicate_class(
                teacher_id=self.teacher.pk,
                grade_level=grade_level,
                strand=strand,
                section=section,
                exclude_id=self.class_id
            )

            if is_duplicate:
                raise ValidationError(
                    f"A class with grade level '{grade_level}', strand '{strand}', "
                    f"and section '{section}' already exists for this teacher"
                )

        return cleaned_data


class StudentClassAssignmentForm(forms.Form):
    """
    Form for assigning individual students to classes.
    Requirements: 2.1
    """
    student = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Student'
        }),
        error_messages={
            'required': 'Please select a student',
            'invalid_choice': 'Please select a valid student'
        }
    )
    
    class_assigned = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Class'
        }),
        error_messages={
            'required': 'Please select a class',
            'invalid_choice': 'Please select a valid class'
        }
    )
    
    def __init__(self, *args, teacher=None, **kwargs):
        """
        Initialize form with teacher-specific class queryset.
        
        Args:
            teacher: Teacher instance to filter classes
        """
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from users.models import Student, Class
        
        # Set student queryset (all students)
        self.fields['student'].queryset = Student.objects.all().order_by('last_name', 'first_name')
        
        # Set class queryset (only classes belonging to the teacher)
        if teacher:
            self.fields['class_assigned'].queryset = Class.objects.filter(
                teacher=teacher
            ).order_by('grade_level', 'strand', 'section')
        else:
            self.fields['class_assigned'].queryset = Class.objects.none()


class BulkStudentAssignmentForm(forms.Form):
    """
    Form for bulk assigning multiple students to a class.
    Requirements: 8.1, 8.2
    """
    students = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set in __init__
        required=True,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded',
        }),
        error_messages={
            'required': 'Please select at least one student',
            'invalid_choice': 'Please select valid students'
        }
    )
    
    class_assigned = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=True,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Class'
        }),
        error_messages={
            'required': 'Please select a class',
            'invalid_choice': 'Please select a valid class'
        }
    )
    
    def __init__(self, *args, teacher=None, initial_class_id=None, **kwargs):
        """
        Initialize form with teacher-specific class queryset.
        
        Args:
            teacher: Teacher instance to filter classes
            initial_class_id: Optional class ID to pre-select
        """
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from users.models import Student, Class

        # Set students queryset - exclude students already in the target class
        students_qs = Student.objects.all().order_by('last_name', 'first_name')
        if initial_class_id:
            students_qs = students_qs.exclude(class_assigned_id=initial_class_id)
        self.fields['students'].queryset = students_qs
        
        # Set class queryset (only classes belonging to the teacher)
        if teacher:
            self.fields['class_assigned'].queryset = Class.objects.filter(
                teacher=teacher
            ).order_by('grade_level', 'strand', 'section')
            
            # Pre-select class if initial_class_id is provided
            if initial_class_id and not self.data:
                try:
                    selected_class = Class.objects.get(id=initial_class_id, teacher=teacher)
                    self.fields['class_assigned'].initial = selected_class
                    # Make the field read-only by disabling it visually (we'll handle this in the template)
                    self.fields['class_assigned'].widget.attrs['data-preselected'] = 'true'
                except Class.DoesNotExist:
                    pass
        else:
            self.fields['class_assigned'].queryset = Class.objects.none()


class StudentCreationForm(forms.Form):
    """
    Form for manually creating student accounts.
    Password is auto-generated based on ID number and last name.
    """
    school_id = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'e.g., 2024-0001',
            'data-field-name': 'Student ID Number'
        }),
        error_messages={
            'required': 'Student ID number is required',
            'max_length': 'Student ID must not exceed 50 characters'
        }
    )
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'First Name',
            'data-field-name': 'First Name'
        }),
        error_messages={
            'required': 'First name is required',
            'max_length': 'First name must not exceed 100 characters'
        }
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'placeholder': 'Last Name',
            'data-field-name': 'Last Name'
        }),
        error_messages={
            'required': 'Last name is required',
            'max_length': 'Last name must not exceed 100 characters'
        }
    )
    
    class_assigned = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
            'data-field-name': 'Class (Optional)'
        }),
        error_messages={
            'invalid_choice': 'Please select a valid class'
        }
    )
    
    def __init__(self, *args, teacher=None, **kwargs):
        """
        Initialize form with teacher-specific class queryset.
        
        Args:
            teacher: Teacher instance to filter classes
        """
        super().__init__(*args, **kwargs)
        
        # Import here to avoid circular imports
        from users.models import Class
        
        # Set class queryset (only classes belonging to the teacher)
        if teacher:
            self.fields['class_assigned'].queryset = Class.objects.filter(
                teacher=teacher
            ).order_by('grade_level', 'strand', 'section')
        else:
            self.fields['class_assigned'].queryset = Class.objects.none()
    
    def clean_school_id(self):
        """Validate and clean School ID field."""
        from users.models import Student
        
        school_id = self.cleaned_data.get('school_id', '').strip()
        
        if not school_id:
            raise ValidationError('Student ID cannot be empty')
        
        # Check if school_id already exists
        if Student.objects.filter(school_id=school_id).exists():
            raise ValidationError(f'A student with ID "{school_id}" already exists')
        
        return school_id
    
    def clean_first_name(self):
        """Validate and clean first name field."""
        first_name = self.cleaned_data.get('first_name', '').strip()
        
        if not first_name:
            raise ValidationError('First name cannot be empty')
        
        return first_name
    
    def clean_last_name(self):
        """Validate and clean last name field."""
        last_name = self.cleaned_data.get('last_name', '').strip()
        
        if not last_name:
            raise ValidationError('Last name cannot be empty')
        
        return last_name
    
    @staticmethod
    def generate_password(school_id, last_name):
        """
        Generate password based on ID number and last name.
        Password format: First 4 digits of ID + First 4 letters of last name (uppercase)
        
        Args:
            school_id: Student ID number
            last_name: Student last name
            
        Returns:
            Generated password string
        """
        # Extract first 4 digits from school_id
        digits = ''.join(filter(str.isdigit, school_id))[:4]
        
        # If less than 4 digits, pad with zeros
        if len(digits) < 4:
            digits = digits.ljust(4, '0')
        
        # Extract first 4 letters from last_name (uppercase, letters only)
        letters = ''.join(filter(str.isalpha, last_name))[:4].upper()
        
        # If less than 4 letters, pad with 'X'
        if len(letters) < 4:
            letters = letters.ljust(4, 'X')
        
        return digits + letters
