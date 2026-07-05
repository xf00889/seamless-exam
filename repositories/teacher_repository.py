from typing import Optional
from django.contrib.auth.models import User
from .base_repository import BaseRepository
from users.models import Teacher


class TeacherRepository(BaseRepository):
    def __init__(self):
        super().__init__(Teacher)

    def get_by_user_id(self, user_id: int) -> Optional[Teacher]:
        try:
            return self.model.objects.get(user_id=user_id)
        except self.model.DoesNotExist:
            return None

    def get_by_username(self, username: str) -> Optional[Teacher]:
        try:
            user = User.objects.get(username=username)
            return self.model.objects.get(user=user)
        except (User.DoesNotExist, self.model.DoesNotExist):
            return None

    def create_teacher(
        self, username: str, password: str, school_id: int,
        email: str = '', first_name: str = '', last_name: str = '',
        department: str = ''
    ) -> Teacher:
        from users.models import School
        user = User.objects.create_user(
            username=username, password=password, email=email,
            first_name=first_name, last_name=last_name,
        )
        teacher = Teacher.objects.create(
            user=user, school_id=school_id, department=department,
        )
        return teacher

    def update_teacher(self, user_id: int, **kwargs) -> Optional[Teacher]:
        teacher = self.get_by_user_id(user_id)
        if not teacher:
            return None
        user_fields = {'email', 'first_name', 'last_name'}
        teacher_updates = {}
        user_updates = {}
        for key, value in kwargs.items():
            if key in user_fields:
                user_updates[key] = value
            else:
                teacher_updates[key] = value
        if user_updates:
            for key, value in user_updates.items():
                setattr(teacher.user, key, value)
            teacher.user.save()
        if teacher_updates:
            for key, value in teacher_updates.items():
                setattr(teacher, key, value)
            teacher.save()
        return teacher

    def username_exists(self, username: str) -> bool:
        return User.objects.filter(username=username).exists()
