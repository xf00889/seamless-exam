"""
Class service for business logic operations.
Handles class CRUD operations, student assignments, and exam-class associations.
"""
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import QuerySet, Avg, Count
from users.models import Class, Student, Teacher
from exams.models import Exam, ExamClassAssignment
from attempts.models import Attempt
from repositories.class_repository import ClassRepository
from repositories.exam_repository import ExamRepository
from repositories.student_repository import StudentRepository
from services.result import Result


class ClassService:
    """
    Service class for class-related business logic.
    Handles class creation, updates, student assignments, and exam associations.
    """
    
    def __init__(self):
        self.class_repository = ClassRepository()
        self.exam_repository = ExamRepository()
        self.student_repository = StudentRepository()
    
    def create_class(
        self,
        teacher_id: int,
        grade_level: str,
        strand: str,
        section: str
    ) -> Result[Class, str]:
        """
        Create a new class with validation.
        
        Validates that all required fields are present and that no duplicate
        class exists for the teacher with the same grade_level, strand, and section.
        
        Args:
            teacher_id: Primary key of the teacher creating the class
            grade_level: Grade level (e.g., "Grade 11", "Grade 12")
            strand: Academic strand (e.g., "HUMSS", "GAS", "ABM")
            section: Section name (e.g., "A", "B", "Einstein")
            
        Returns:
            Result[Class, str]: Success with created Class or Failure with error message
            
        Requirements: 1.1, 1.2, 7.1
        """
        # Validate required fields
        if not grade_level or not grade_level.strip():
            return Result.failure("Grade level is required")
        if not strand or not strand.strip():
            return Result.failure("Strand is required")
        if not section or not section.strip():
            return Result.failure("Section is required")
        
        # Check for duplicate class
        if self.class_repository.check_duplicate_class(
            teacher_id=teacher_id,
            grade_level=grade_level.strip(),
            strand=strand.strip(),
            section=section.strip()
        ):
            return Result.failure(
                f"A class with grade level '{grade_level}', strand '{strand}', "
                f"and section '{section}' already exists for this teacher"
            )
        
        # Verify teacher exists
        try:
            teacher = Teacher.objects.get(pk=teacher_id)
        except Teacher.DoesNotExist:
            return Result.failure(f"Teacher with ID {teacher_id} not found")
        
        # Create the class
        try:
            class_obj = self.class_repository.create(
                teacher=teacher,
                grade_level=grade_level.strip(),
                strand=strand.strip(),
                section=section.strip()
            )
            return Result.success(class_obj)
        except Exception as e:
            return Result.failure(f"Failed to create class: {str(e)}")
    
    def update_class(
        self,
        class_id: int,
        grade_level: str,
        strand: str,
        section: str
    ) -> Result[Class, str]:
        """
        Update an existing class with uniqueness validation.
        
        Validates that the updated values don't conflict with other classes
        by the same teacher, excluding the current class being edited.
        
        Args:
            class_id: Primary key of the class to update
            grade_level: New grade level
            strand: New strand
            section: New section
            
        Returns:
            Result[Class, str]: Success with updated Class or Failure with error message
            
        Requirements: 1.4, 7.3
        """
        # Validate required fields
        if not grade_level or not grade_level.strip():
            return Result.failure("Grade level is required")
        if not strand or not strand.strip():
            return Result.failure("Strand is required")
        if not section or not section.strip():
            return Result.failure("Section is required")
        
        # Get existing class
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        # Check for duplicate class (excluding current class)
        if self.class_repository.check_duplicate_class(
            teacher_id=class_obj.teacher_id,
            grade_level=grade_level.strip(),
            strand=strand.strip(),
            section=section.strip(),
            exclude_id=class_id
        ):
            return Result.failure(
                f"A class with grade level '{grade_level}', strand '{strand}', "
                f"and section '{section}' already exists for this teacher"
            )
        
        # Update the class
        try:
            updated_class = self.class_repository.update(
                class_id,
                grade_level=grade_level.strip(),
                strand=strand.strip(),
                section=section.strip()
            )
            if updated_class:
                return Result.success(updated_class)
            return Result.failure(f"Failed to update class with ID {class_id}")
        except Exception as e:
            return Result.failure(f"Failed to update class: {str(e)}")
    
    def delete_class(self, class_id: int) -> Result[bool, str]:
        """
        Delete a class.
        
        Deletes the class and updates all associated student records to have
        null class assignments (due to SET_NULL on the foreign key).
        
        Args:
            class_id: Primary key of the class to delete
            
        Returns:
            Result[bool, str]: Success with True or Failure with error message
            
        Requirements: 1.5
        """
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        # Delete the class (CASCADE will handle ExamClassAssignment, SET_NULL for students)
        try:
            deleted = self.class_repository.delete(class_id)
            if deleted:
                return Result.success(True)
            return Result.failure(f"Failed to delete class with ID {class_id}")
        except Exception as e:
            return Result.failure(f"Failed to delete class: {str(e)}")

    def assign_student_to_class(
        self,
        student_id: int,
        class_id: int
    ) -> Result[Student, str]:
        """
        Assign a student to a class.
        
        Ensures single class assignment by replacing any existing class assignment.
        If the student is already assigned to a class, the assignment is updated.
        
        Args:
            student_id: Primary key of the student
            class_id: Primary key of the class
            
        Returns:
            Result[Student, str]: Success with updated Student or Failure with error message
            
        Requirements: 2.1, 2.2
        """
        # Verify student exists
        student = self.student_repository.get_by_id(student_id)
        if not student:
            return Result.failure(f"Student with ID {student_id} not found")
        
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        # Assign student to class (replaces existing assignment)
        try:
            updated_student = self.student_repository.update(
                student_id,
                class_assigned=class_obj
            )
            if updated_student:
                return Result.success(updated_student)
            return Result.failure(f"Failed to assign student to class")
        except Exception as e:
            return Result.failure(f"Failed to assign student: {str(e)}")
    
    def remove_student_from_class(self, student_id: int) -> Result[Student, str]:
        """
        Remove a student from their assigned class.
        
        Sets the student's class_assigned field to null while preserving
        all historical exam attempts.
        
        Args:
            student_id: Primary key of the student
            
        Returns:
            Result[Student, str]: Success with updated Student or Failure with error message
            
        Requirements: 2.4, 2.5
        """
        # Verify student exists
        student = self.student_repository.get_by_id(student_id)
        if not student:
            return Result.failure(f"Student with ID {student_id} not found")
        
        # Remove class assignment (set to null)
        try:
            updated_student = self.student_repository.update(
                student_id,
                class_assigned=None
            )
            if updated_student:
                return Result.success(updated_student)
            return Result.failure(f"Failed to remove student from class")
        except Exception as e:
            return Result.failure(f"Failed to remove student: {str(e)}")

    def bulk_assign_students(
        self,
        student_ids: List[int],
        class_id: int
    ) -> Result[Dict[str, Any], str]:
        """
        Bulk assign multiple students to a class in a single transaction.
        
        All assignments succeed or all fail (atomicity). Returns a summary
        of successful and failed assignments.
        
        Args:
            student_ids: List of student primary keys
            class_id: Primary key of the class
            
        Returns:
            Result[Dict, str]: Success with summary dict or Failure with error message
            Summary dict contains:
                - total: Total number of students
                - successful: Number of successful assignments
                - failed: Number of failed assignments
                - errors: List of error messages for failed assignments
            
        Requirements: 8.3, 8.4, 8.5
        """
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        if not student_ids:
            return Result.failure("No students provided for bulk assignment")
        
        # Use transaction for atomicity
        try:
            with transaction.atomic():
                successful = 0
                failed = 0
                errors = []
                
                for student_id in student_ids:
                    # Verify student exists
                    student = self.student_repository.get_by_id(student_id)
                    if not student:
                        errors.append(f"Student with ID {student_id} not found")
                        failed += 1
                        # Rollback transaction on any failure
                        raise Exception(f"Student with ID {student_id} not found")
                    
                    # Assign student to class
                    updated_student = self.student_repository.update(
                        student_id,
                        class_assigned=class_obj
                    )
                    if updated_student:
                        successful += 1
                    else:
                        errors.append(f"Failed to assign student {student_id}")
                        failed += 1
                        # Rollback transaction on any failure
                        raise Exception(f"Failed to assign student {student_id}")
                
                # If we reach here, all assignments succeeded
                return Result.success({
                    'total': len(student_ids),
                    'successful': successful,
                    'failed': failed,
                    'errors': errors
                })
        except Exception as e:
            # Transaction rolled back, all assignments failed
            return Result.failure(
                f"Bulk assignment failed: {str(e)}. All changes have been rolled back."
            )

    def assign_exam_to_classes(
        self,
        exam_id: int,
        class_ids: List[int]
    ) -> Result[List[ExamClassAssignment], str]:
        """
        Assign an exam to multiple classes.
        
        Creates ExamClassAssignment records for each class. Skips classes
        that are already assigned to avoid duplicate assignments.
        
        Args:
            exam_id: Primary key of the exam
            class_ids: List of class primary keys
            
        Returns:
            Result[List[ExamClassAssignment], str]: Success with list of assignments
                or Failure with error message
            
        Requirements: 3.1
        """
        # Verify exam exists
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
                    # Verify class exists
                    class_obj = self.class_repository.get_by_id(class_id)
                    if not class_obj:
                        errors.append(f"Class with ID {class_id} not found")
                        continue
                    
                    # Check if assignment already exists
                    existing = ExamClassAssignment.objects.filter(
                        exam_id=exam_id,
                        class_assigned_id=class_id
                    ).first()
                    
                    if existing:
                        # Skip duplicate assignment
                        assignments.append(existing)
                    else:
                        # Create new assignment
                        assignment = ExamClassAssignment.objects.create(
                            exam=exam,
                            class_assigned=class_obj
                        )
                        assignments.append(assignment)
                
                if errors:
                    return Result.failure(
                        f"Some classes could not be assigned: {', '.join(errors)}"
                    )
                
                return Result.success(assignments)
        except Exception as e:
            return Result.failure(f"Failed to assign exam to classes: {str(e)}")
    
    def remove_exam_from_class(
        self,
        exam_id: int,
        class_id: int
    ) -> Result[bool, str]:
        """
        Remove an exam assignment from a class.
        
        Deletes the ExamClassAssignment record, preventing students in that
        class from accessing the exam.
        
        Args:
            exam_id: Primary key of the exam
            class_id: Primary key of the class
            
        Returns:
            Result[bool, str]: Success with True or Failure with error message
            
        Requirements: 3.5
        """
        # Verify exam exists
        exam = self.exam_repository.get_by_id(exam_id)
        if not exam:
            return Result.failure(f"Exam with ID {exam_id} not found")
        
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        # Find and delete the assignment
        try:
            assignment = ExamClassAssignment.objects.filter(
                exam_id=exam_id,
                class_assigned_id=class_id
            ).first()
            
            if not assignment:
                return Result.failure(
                    f"No assignment found between exam {exam_id} and class {class_id}"
                )
            
            assignment.delete()
            return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to remove exam from class: {str(e)}")
    
    def get_exams_for_class(self, class_id: int) -> Result[QuerySet, str]:
        """
        Retrieve all exams assigned to a specific class.
        
        Args:
            class_id: Primary key of the class
            
        Returns:
            Result[QuerySet, str]: Success with QuerySet of Exams or Failure with error message
            
        Requirements: 3.4
        """
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        try:
            exams = self.exam_repository.get_exams_for_class(class_id)
            return Result.success(exams)
        except Exception as e:
            return Result.failure(f"Failed to retrieve exams for class: {str(e)}")

    def get_class_statistics(self, class_id: int) -> Result[Dict[str, Any], str]:
        """
        Calculate statistics for a specific class.
        
        Computes student count, average scores, and filters attempts by class.
        
        Args:
            class_id: Primary key of the class
            
        Returns:
            Result[Dict, str]: Success with statistics dict or Failure with error message
            Statistics dict contains:
                - student_count: Number of students in the class
                - average_score: Average score across all attempts by class students
                - total_attempts: Total number of attempts by class students
                - exams_assigned: Number of exams assigned to the class
            
        Requirements: 5.2, 5.3
        """
        # Verify class exists
        class_obj = self.class_repository.get_by_id(class_id)
        if not class_obj:
            return Result.failure(f"Class with ID {class_id} not found")
        
        try:
            # Get student count
            student_count = self.class_repository.get_students_in_class(class_id).count()
            
            # Get attempts by students in this class
            attempts = Attempt.objects.filter(
                student__class_assigned_id=class_id
            )
            
            # Calculate statistics
            total_attempts = attempts.count()
            
            # Calculate average score
            avg_result = attempts.aggregate(avg_score=Avg('score'))
            average_score = avg_result['avg_score'] if avg_result['avg_score'] is not None else 0.0
            
            # Get number of exams assigned to this class
            exams_assigned = ExamClassAssignment.objects.filter(
                class_assigned_id=class_id
            ).count()
            
            return Result.success({
                'student_count': student_count,
                'average_score': float(average_score),
                'total_attempts': total_attempts,
                'exams_assigned': exams_assigned
            })
        except Exception as e:
            return Result.failure(f"Failed to calculate class statistics: {str(e)}")
