from typing import Optional
from django.contrib.auth.models import User
from .base_repository import BaseRepository
from users.models import Student


class StudentRepository(BaseRepository):
    def __init__(self):
        super().__init__(Student)

    def get_by_school_id(self, student_id: str) -> Optional[Student]:
        normalized = (student_id or '').strip()
        if not normalized:
            return None
        try:
            return self.model.objects.get(student_id=normalized)
        except self.model.DoesNotExist:
            matches = list(self.model.objects.filter(
                student_id__iexact=normalized
            )[:2])
            return matches[0] if len(matches) == 1 else None

    def create_student(
        self, student_id: str, first_name: str, last_name: str,
        password: str, school_id: int, created_by: Optional[User] = None
    ) -> Student:
        from users.models import School
        student = Student(
            student_id=student_id,
            first_name=first_name,
            last_name=last_name,
            school_id=school_id,
            created_by=created_by,
        )
        student.set_password(password)
        student.save()
        return student

    def update_password(self, student_id: str, new_password: str) -> Optional[Student]:
        student = self.get_by_school_id(student_id)
        if student:
            student.set_password(new_password)
            student.save()
        return student

    def student_id_exists(self, student_id: str) -> bool:
        return self.exists(student_id=student_id)
