from typing import Optional
from django.db.models import QuerySet
from users.models import Class, Student, GradeLevel, Strand, Section
from repositories.base_repository import BaseRepository


class ClassRepository(BaseRepository):
    def __init__(self):
        super().__init__(Class)

    def get_classes_by_teacher(self, teacher_id: int) -> QuerySet:
        return Class.objects.filter(teachers__user_id=teacher_id).distinct()

    def get_class_with_students(self, class_id: int) -> Optional[Class]:
        try:
            return self.model.objects.prefetch_related('students').get(pk=class_id)
        except self.model.DoesNotExist:
            return None

    def get_students_in_class(self, class_id: int) -> QuerySet:
        return Student.objects.filter(class_assigned_id=class_id)

    def check_duplicate_class(
        self,
        school_id: int,
        grade_level_id: int,
        strand_id: int,
        section_id: int,
        exclude_id: Optional[int] = None
    ) -> bool:
        queryset = self.filter(
            school_id=school_id,
            grade_level_id=grade_level_id,
            strand_id=strand_id,
            section_id=section_id,
        )
        if exclude_id is not None:
            queryset = queryset.exclude(pk=exclude_id)
        return queryset.exists()

    def get_classes_by_strand(self, strand_id: int) -> QuerySet:
        return self.filter(strand_id=strand_id).select_related('school')

    def get_classes_by_grade(self, grade_level_id: int) -> QuerySet:
        return self.filter(grade_level_id=grade_level_id).select_related('school')
