from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import QuerySet, Avg, Count
from users.models import Class, Student, Teacher, GradeLevel, Strand, Section, School
from exams.models import Exam, ExamClassAssignment
from attempts.models import Attempt
from repositories.class_repository import ClassRepository
from repositories.exam_repository import ExamRepository
from repositories.student_repository import StudentRepository
from services.result import Result


class ClassService:
    def __init__(self):
        self.class_repository = ClassRepository()
        self.exam_repository = ExamRepository()
        self.student_repository = StudentRepository()

    def create_class(
        self,
        school_id: int,
        grade_level_id: int,
        strand_id: int,
        section_id: int,
        teacher_ids: Optional[List[int]] = None,
    ) -> Result[Class, str]:
        if not grade_level_id:
            return Result.failure("Grade level is required")
        if not strand_id:
            return Result.failure("Strand is required")
        if not section_id:
            return Result.failure("Section is required")

        if self.class_repository.check_duplicate_class(
            school_id=school_id,
            grade_level_id=grade_level_id,
            strand_id=strand_id,
            section_id=section_id,
        ):
            return Result.failure("A class with these details already exists in this school")

        try:
            school = School.objects.get(pk=school_id)
            grade_level = GradeLevel.objects.get(pk=grade_level_id)
            strand = Strand.objects.get(pk=strand_id)
            section = Section.objects.get(pk=section_id)
        except (School.DoesNotExist, GradeLevel.DoesNotExist,
                Strand.DoesNotExist, Section.DoesNotExist) as e:
            return Result.failure(str(e))

        try:
            with transaction.atomic():
                class_obj = self.class_repository.create(
                    school=school,
                    grade_level=grade_level,
                    strand=strand,
                    section=section,
                )
                if teacher_ids:
                    teachers = Teacher.objects.filter(pk__in=teacher_ids, school_id=school_id)
                    class_obj.teachers.add(*teachers)
                return Result.success(class_obj)
        except Exception as e:
            return Result.failure(f"Failed to create class: {str(e)}")

    def update_class(
        self,
        class_id: int,
        grade_level_id: int,
        strand_id: int,
        section_id: int,
    ) -> Result[Class, str]:
        if not grade_level_id:
            return Result.failure("Grade level is required")
        if not strand_id:
            return Result.failure("Strand is required")
        if not section_id:
            return Result.failure("Section is required")

        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")

        if self.class_repository.check_duplicate_class(
            school_id=class_obj.school_id,
            grade_level_id=grade_level_id,
            strand_id=strand_id,
            section_id=section_id,
            exclude_id=class_id,
        ):
            return Result.failure("A class with these details already exists in this school")

        try:
            grade_level = GradeLevel.objects.get(pk=grade_level_id)
            strand = Strand.objects.get(pk=strand_id)
            section = Section.objects.get(pk=section_id)
            updated_class = self.class_repository.update(
                class_id,
                grade_level=grade_level,
                strand=strand,
                section=section,
            )
            if updated_class:
                return Result.success(updated_class)
            return Result.failure(f"Failed to update class with ID {class_id}")
        except Exception as e:
            return Result.failure(f"Failed to update class: {str(e)}")

    def delete_class(self, class_id: int) -> Result[bool, str]:
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        try:
            deleted = self.class_repository.delete(class_id)
            if deleted:
                return Result.success(True)
            return Result.failure(f"Failed to delete class with ID {class_id}")
        except Exception as e:
            return Result.failure(f"Failed to delete class: {str(e)}")

    def assign_student_to_class(self, student_id: int, class_id: int) -> Result[Student, str]:
        student = self.student_repository.get_by_id(student_id)
        if not student:
            return Result.failure(f"Student with ID {student_id} not found")
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        try:
            updated_student = self.student_repository.update(
                student_id, class_assigned=class_obj
            )
            if updated_student:
                return Result.success(updated_student)
            return Result.failure(f"Failed to assign student to class")
        except Exception as e:
            return Result.failure(f"Failed to assign student: {str(e)}")

    def remove_student_from_class(self, student_id: int) -> Result[Student, str]:
        student = self.student_repository.get_by_id(student_id)
        if not student:
            return Result.failure(f"Student with ID {student_id} not found")
        try:
            updated_student = self.student_repository.update(
                student_id, class_assigned=None
            )
            if updated_student:
                return Result.success(updated_student)
            return Result.failure(f"Failed to remove student from class")
        except Exception as e:
            return Result.failure(f"Failed to remove student: {str(e)}")

    def bulk_assign_students(self, student_ids: List[int], class_id: int) -> Result[Dict[str, Any], str]:
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        if not student_ids:
            return Result.failure("No students provided for bulk assignment")
        try:
            with transaction.atomic():
                successful = 0
                for student_id in student_ids:
                    student = self.student_repository.get_by_id(student_id)
                    if not student:
                        raise Exception(f"Student with ID {student_id} not found")
                    updated = self.student_repository.update(student_id, class_assigned=class_obj)
                    if updated:
                        successful += 1
                    else:
                        raise Exception(f"Failed to assign student {student_id}")
                return Result.success({
                    'total': len(student_ids),
                    'successful': successful,
                    'failed': len(student_ids) - successful,
                    'errors': [],
                })
        except Exception as e:
            return Result.failure(f"Bulk assignment failed: {str(e)}. All changes have been rolled back.")

    def assign_exam_to_classes(self, exam_id: int, class_ids: List[int]) -> Result[List[ExamClassAssignment], str]:
        exam = self.exam_repository.get_by_id(exam_id)
        if not exam:
            return Result.failure(f"Exam with ID {exam_id} not found")
        if not class_ids:
            return Result.failure("No classes provided for exam assignment")
        assignments = []
        errors = []
        try:
            with transaction.atomic():
                for class_id in class_ids:
                    class_obj = self.class_repository.get_by_id(class_id)
                    if not class_obj:
                        errors.append(f"Class with ID {class_id} not found")
                        continue
                    existing = ExamClassAssignment.objects.filter(
                        exam_id=exam_id, class_assigned_id=class_id
                    ).first()
                    if existing:
                        assignments.append(existing)
                    else:
                        assignment = ExamClassAssignment.objects.create(
                            exam=exam, class_assigned=class_obj
                        )
                        assignments.append(assignment)
                if errors:
                    return Result.failure(f"Some classes could not be assigned: {', '.join(errors)}")
                return Result.success(assignments)
        except Exception as e:
            return Result.failure(f"Failed to assign exam to classes: {str(e)}")

    def remove_exam_from_class(self, exam_id: int, class_id: int) -> Result[bool, str]:
        exam = self.exam_repository.get_by_id(exam_id)
        if not exam:
            return Result.failure(f"Exam with ID {exam_id} not found")
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        try:
            assignment = ExamClassAssignment.objects.filter(
                exam_id=exam_id, class_assigned_id=class_id
            ).first()
            if not assignment:
                return Result.failure(f"No assignment found between exam {exam_id} and class {class_id}")
            assignment.delete()
            return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to remove exam from class: {str(e)}")

    def get_exams_for_class(self, class_id: int) -> Result[QuerySet, str]:
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        try:
            exams = self.exam_repository.get_exams_for_class(class_id)
            return Result.success(exams)
        except Exception as e:
            return Result.failure(f"Failed to retrieve exams for class: {str(e)}")

    def get_class_statistics(self, class_id: int) -> Result[Dict[str, Any], str]:
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        try:
            student_count = self.class_repository.get_students_in_class(class_id).count()
            attempts = Attempt.objects.filter(student__class_assigned_id=class_id)
            total_attempts = attempts.count()
            avg_result = attempts.aggregate(avg_score=Avg('score'))
            average_score = avg_result['avg_score'] if avg_result['avg_score'] is not None else 0.0
            exams_assigned = ExamClassAssignment.objects.filter(
                class_assigned_id=class_id
            ).count()
            return Result.success({
                'student_count': student_count,
                'average_score': float(average_score),
                'total_attempts': total_attempts,
                'exams_assigned': exams_assigned,
            })
        except Exception as e:
            return Result.failure(f"Failed to calculate class statistics: {str(e)}")
