"""
Management command to create test teacher and student accounts.

Usage:
    python manage.py create_test_accounts
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import Teacher, Student
from django.db import transaction


class Command(BaseCommand):
    help = 'Creates test teacher and student accounts for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing test accounts before creating new ones',
        )

    def handle(self, *args, **options):
        """Create test accounts."""
        
        reset = options.get('reset', False)
        
        self.stdout.write(self.style.WARNING('\n=== Creating Test Accounts ===\n'))
        
        # Test account credentials
        test_accounts = {
            'teacher': {
                'username': 'teacher',
                'password': 'teacher123',
                'email': 'teacher@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'department': 'Computer Science'
            },
            'students': [
                {
                    'school_id': 'STU001',
                    'password': 'student123',
                    'first_name': 'Alice',
                    'last_name': 'Smith'
                },
                {
                    'school_id': 'STU002',
                    'password': 'student123',
                    'first_name': 'Bob',
                    'last_name': 'Johnson'
                },
                {
                    'school_id': 'STU003',
                    'password': 'student123',
                    'first_name': 'Charlie',
                    'last_name': 'Williams'
                }
            ]
        }
        
        try:
            with transaction.atomic():
                # Create Teacher Account
                self.stdout.write('\n1. Creating Teacher Account...')
                
                teacher_data = test_accounts['teacher']
                
                if reset:
                    # Delete existing teacher account
                    User.objects.filter(username=teacher_data['username']).delete()
                    self.stdout.write(self.style.WARNING('   Deleted existing teacher account'))
                
                # Check if teacher already exists
                if User.objects.filter(username=teacher_data['username']).exists():
                    self.stdout.write(self.style.WARNING(
                        f'   Teacher account "{teacher_data["username"]}" already exists. Skipping.'
                    ))
                else:
                    # Create Django User
                    user = User.objects.create_user(
                        username=teacher_data['username'],
                        password=teacher_data['password'],
                        email=teacher_data['email'],
                        first_name=teacher_data['first_name'],
                        last_name=teacher_data['last_name']
                    )
                    
                    # Create Teacher profile
                    teacher = Teacher.objects.create(
                        user=user,
                        department=teacher_data['department']
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f'   ✓ Created teacher account: {teacher_data["username"]}'
                    ))
                
                # Create Student Accounts
                self.stdout.write('\n2. Creating Student Accounts...')
                
                for student_data in test_accounts['students']:
                    if reset:
                        # Delete existing student account
                        Student.objects.filter(school_id=student_data['school_id']).delete()
                    
                    # Check if student already exists
                    if Student.objects.filter(school_id=student_data['school_id']).exists():
                        self.stdout.write(self.style.WARNING(
                            f'   Student "{student_data["school_id"]}" already exists. Skipping.'
                        ))
                    else:
                        # Create Student
                        student = Student.objects.create(
                            school_id=student_data['school_id'],
                            first_name=student_data['first_name'],
                            last_name=student_data['last_name']
                        )
                        student.set_password(student_data['password'])
                        student.save()
                        
                        self.stdout.write(self.style.SUCCESS(
                            f'   ✓ Created student: {student_data["school_id"]} - {student.get_full_name()}'
                        ))
                
                # Display credentials
                self.stdout.write(self.style.SUCCESS('\n=== Test Accounts Created Successfully ===\n'))
                
                self.stdout.write(self.style.WARNING('TEACHER CREDENTIALS:'))
                self.stdout.write(f'  Username: {test_accounts["teacher"]["username"]}')
                self.stdout.write(f'  Password: {test_accounts["teacher"]["password"]}')
                self.stdout.write(f'  URL: http://localhost:8000/teacher/login/\n')
                
                self.stdout.write(self.style.WARNING('STUDENT CREDENTIALS:'))
                for student_data in test_accounts['students']:
                    self.stdout.write(
                        f'  School ID: {student_data["school_id"]} | '
                        f'Password: {student_data["password"]} | '
                        f'Name: {student_data["first_name"]} {student_data["last_name"]}'
                    )
                self.stdout.write(f'  URL: http://localhost:8000/student/login/\n')
                
                self.stdout.write(self.style.SUCCESS('Ready to test the application!\n'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nError creating test accounts: {str(e)}'))
            raise
