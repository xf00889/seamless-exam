from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from users.models import School, SchoolAdmin


class Command(BaseCommand):
    help = 'Creates a school admin user for a given school'

    def add_arguments(self, parser):
        parser.add_argument('--school', required=True, help='School ID or name')
        parser.add_argument('--username', required=True, help='Admin username')
        parser.add_argument('--password', required=True, help='Admin password')
        parser.add_argument('--email', default='', help='Admin email')
        parser.add_argument('--first-name', default='', help='Admin first name')
        parser.add_argument('--last-name', default='', help='Admin last name')

    def handle(self, *args, **options):
        school_arg = options['school']
        username = options['username']
        password = options['password']
        email = options['email']
        first_name = options['first_name']
        last_name = options['last_name']

        try:
            school = School.objects.get(pk=int(school_arg))
        except (ValueError, School.DoesNotExist):
            try:
                school = School.objects.get(name=school_arg)
            except School.DoesNotExist:
                raise CommandError(f'School not found: "{school_arg}"')

        if User.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists')

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        SchoolAdmin.objects.create(user=user, school=school)

        self.stdout.write(self.style.SUCCESS(
            f'School admin "{username}" created for school "{school.name}"'
        ))
