"""
Dashboard service for student performance analytics.
Provides methods for retrieving performance metrics, score trends, and exam history.
Implements caching for performance optimization (Requirements 11.1, 11.5).
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal
from django.db.models import Avg, Max, Min, Count, Q, F
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
import csv
import io
import logging

from repositories.attempt_repository import AttemptRepository
from repositories.student_repository import StudentRepository
from services.result import Result
from services.errors import NotFoundError, ValidationError
from attempts.models import Attempt, AttemptStatus, Answer
from exams.models import QuestionType

logger = logging.getLogger('services')


class DashboardService:
    """
    Service for managing student dashboard analytics.
    Provides performance metrics, score trends, and exam history.
    Implements caching for performance optimization (Requirements 11.1, 11.5).
    """
    
    def __init__(self):
        """Initialize with required repositories."""
        self.attempt_repo = AttemptRepository()
        self.student_repo = StudentRepository()
    
    @staticmethod
    def _get_cache_key(key_template: str, student_id: int) -> str:
        """
        Generate cache key for a student's data.
        
        Args:
            key_template: Cache key template from settings
            student_id: Student's database ID
            
        Returns:
            str: Formatted cache key
        """
        return key_template.format(student_id=student_id)
    
    @staticmethod
    def invalidate_student_cache(student_id: int) -> None:
        """
        Invalidate all cached data for a student.
        
        Called when a student completes an exam or receives a grade.
        This ensures dashboard data is refreshed after exam completion.
        
        Args:
            student_id: Student's database ID
            
        Requirements: 11.1, 11.5
        """
        cache_keys = [
            DashboardService._get_cache_key(settings.CACHE_KEY_DASHBOARD_METRICS, student_id),
            DashboardService._get_cache_key(settings.CACHE_KEY_SCORE_TREND, student_id),
            DashboardService._get_cache_key(settings.CACHE_KEY_TYPE_PERFORMANCE, student_id),
        ]
        
        cache.delete_many(cache_keys)
        logger.info(f"Cache invalidated for student {student_id}")
    
    @staticmethod
    def warm_cache(student_id: int) -> None:
        """
        Pre-populate cache with frequently accessed data.
        
        Can be called after cache invalidation to ensure fast subsequent access.
        
        Args:
            student_id: Student's database ID
            
        Requirements: 11.1, 11.5
        """
        service = DashboardService()
        
        # Warm up metrics cache
        service.get_performance_metrics(student_id)
        
        # Warm up score trend cache
        service.get_score_trend(student_id)
        
        # Warm up type performance cache
        service.get_type_performance(student_id)
        
        logger.info(f"Cache warmed for student {student_id}")
    
    def get_performance_metrics(self, student_id: int) -> Result[Dict[str, Any], NotFoundError]:
        """
        Calculate and retrieve performance metrics for a student.
        
        Computes:
        - Total number of exams taken (graded only)
        - Average score across all exams
        - Highest score achieved
        - Pass rate (percentage of exams with score >= 60%)
        
        Uses caching with 5-minute TTL for performance optimization.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[Dict, NotFoundError]: Success with metrics dict or Failure with error
            
        Requirements: 7.1, 7.2, 7.3, 7.4, 11.1, 11.5
        """
        # Check cache first
        cache_key = self._get_cache_key(settings.CACHE_KEY_DASHBOARD_METRICS, student_id)
        cached_metrics = cache.get(cache_key)
        
        if cached_metrics is not None:
            logger.debug(f"Cache hit for dashboard metrics: student {student_id}")
            return Result.success(cached_metrics)
        
        logger.debug(f"Cache miss for dashboard metrics: student {student_id}")
        
        try:
            # Verify student exists
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                logger.warning(f"Student not found for metrics: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Get all graded attempts for the student
            graded_attempts = self.attempt_repo.get_by_student(student_id).filter(
                status=AttemptStatus.GRADED
            ).select_related('exam')
            
            # Calculate metrics
            total_exams = graded_attempts.count()
            
            if total_exams == 0:
                # Return empty metrics for students with no graded exams
                metrics = {
                    'total_exams': 0,
                    'average_score': 0.0,
                    'highest_score': 0.0,
                    'pass_rate': 0.0
                }
                # Cache the empty metrics
                cache.set(cache_key, metrics, settings.CACHE_TIMEOUT_DASHBOARD_METRICS)
                logger.info(f"No graded exams found for student {student_id}")
                return Result.success(metrics)
            
            # Calculate average score
            avg_result = graded_attempts.aggregate(avg_score=Avg('total_score'))
            average_score = float(avg_result['avg_score'] or 0.0)
            
            # Calculate highest score
            max_result = graded_attempts.aggregate(max_score=Max('total_score'))
            highest_score = float(max_result['max_score'] or 0.0)
            
            # Calculate pass rate (60% threshold)
            # We need to calculate percentage for each attempt
            passed_count = 0
            for attempt in graded_attempts:
                # Get total possible points from exam
                total_possible = sum(q.points for q in attempt.exam.questions.all())
                if total_possible > 0:
                    percentage = (float(attempt.total_score) / float(total_possible)) * 100
                    if percentage >= 60.0:
                        passed_count += 1
            
            pass_rate = (passed_count / total_exams * 100) if total_exams > 0 else 0.0
            
            metrics = {
                'total_exams': total_exams,
                'average_score': round(average_score, 2),
                'highest_score': round(highest_score, 2),
                'pass_rate': round(pass_rate, 2)
            }
            
            # Cache the metrics with 5-minute TTL
            cache.set(cache_key, metrics, settings.CACHE_TIMEOUT_DASHBOARD_METRICS)
            logger.info(f"Performance metrics calculated and cached for student {student_id}: {metrics}")
            return Result.success(metrics)
            
        except Exception as e:
            logger.error(f"Error calculating performance metrics for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to calculate performance metrics",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def get_score_trend(self, student_id: int) -> Result[List[Dict[str, Any]], NotFoundError]:
        """
        Retrieve score trend data for chart visualization.
        
        Returns a list of exam attempts with dates and scores in chronological order.
        Each entry includes exam name, date, score, and percentage.
        
        Uses caching with 10-minute TTL for performance optimization.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[List[Dict], NotFoundError]: Success with trend data or Failure with error
            
        Requirements: 8.1, 8.2, 11.1, 11.5
        """
        # Check cache first
        cache_key = self._get_cache_key(settings.CACHE_KEY_SCORE_TREND, student_id)
        cached_trend = cache.get(cache_key)
        
        if cached_trend is not None:
            logger.debug(f"Cache hit for score trend: student {student_id}")
            return Result.success(cached_trend)
        
        logger.debug(f"Cache miss for score trend: student {student_id}")
        
        try:
            # Verify student exists
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                logger.warning(f"Student not found for score trend: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Get all graded attempts ordered by submission date
            graded_attempts = self.attempt_repo.get_by_student(student_id).filter(
                status=AttemptStatus.GRADED,
                submitted_at__isnull=False
            ).select_related('exam').order_by('submitted_at')
            
            # Build trend data
            trend_data = []
            for attempt in graded_attempts:
                # Calculate total possible points
                total_possible = sum(q.points for q in attempt.exam.questions.all())
                
                # Calculate percentage
                percentage = 0.0
                if total_possible > 0:
                    percentage = (float(attempt.total_score) / float(total_possible)) * 100
                
                trend_data.append({
                    'exam_name': attempt.exam.title,
                    'date': attempt.submitted_at.isoformat(),
                    'score': float(attempt.total_score),
                    'total_possible': float(total_possible),
                    'percentage': round(percentage, 2)
                })
            
            # Cache the trend data with 10-minute TTL
            cache.set(cache_key, trend_data, settings.CACHE_TIMEOUT_SCORE_TREND)
            logger.info(f"Score trend data retrieved and cached for student {student_id}: {len(trend_data)} entries")
            return Result.success(trend_data)
            
        except Exception as e:
            logger.error(f"Error retrieving score trend for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to retrieve score trend",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def get_type_performance(self, student_id: int) -> Result[Dict[str, float], NotFoundError]:
        """
        Calculate average performance by question type.
        
        Returns average percentage score for each question type (MCQ, Essay, etc.).
        
        Uses caching with 5-minute TTL for performance optimization.
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[Dict[str, float], NotFoundError]: Success with type performance or Failure
            
        Requirements: 9.1, 9.2, 9.3, 11.1, 11.5
        """
        # Check cache first
        cache_key = self._get_cache_key(settings.CACHE_KEY_TYPE_PERFORMANCE, student_id)
        cached_performance = cache.get(cache_key)
        
        if cached_performance is not None:
            logger.debug(f"Cache hit for type performance: student {student_id}")
            return Result.success(cached_performance)
        
        logger.debug(f"Cache miss for type performance: student {student_id}")
        
        try:
            # Verify student exists
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                logger.warning(f"Student not found for type performance: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Get all graded attempts for the student
            graded_attempts = self.attempt_repo.get_by_student(student_id).filter(
                status=AttemptStatus.GRADED
            )
            
            if graded_attempts.count() == 0:
                # Return empty performance for students with no graded exams
                logger.info(f"No graded exams found for type performance: student {student_id}")
                return Result.success({})
            
            # Get all answers for these attempts with question type
            attempt_ids = list(graded_attempts.values_list('id', flat=True))
            answers = Answer.objects.filter(
                attempt_id__in=attempt_ids
            ).select_related('question')
            
            # Group by question type and calculate averages
            type_stats = {}
            for question_type in QuestionType:
                type_answers = [
                    a for a in answers 
                    if a.question.question_type == question_type.value
                ]
                
                if not type_answers:
                    continue
                
                # Calculate average percentage for this type
                total_percentage = 0.0
                count = 0
                
                for answer in type_answers:
                    question_points = float(answer.question.points)
                    if question_points > 0:
                        percentage = (float(answer.points_earned) / question_points) * 100
                        total_percentage += percentage
                        count += 1
                
                if count > 0:
                    avg_percentage = total_percentage / count
                    type_stats[question_type.label] = round(avg_percentage, 2)
            
            # Cache the type performance with 5-minute TTL
            cache.set(cache_key, type_stats, settings.CACHE_TIMEOUT_TYPE_PERFORMANCE)
            logger.info(f"Type performance calculated and cached for student {student_id}: {type_stats}")
            return Result.success(type_stats)
            
        except Exception as e:
            logger.error(f"Error calculating type performance for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to calculate type performance",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def get_recent_activity(
        self, 
        student_id: int, 
        limit: int = 5
    ) -> Result[List[Dict[str, Any]], NotFoundError]:
        """
        Retrieve recent exam activity for a student.
        
        Returns the most recent exam attempts with details.
        Includes both graded and pending attempts.
        
        Args:
            student_id: Student's database ID
            limit: Maximum number of recent activities to return (default: 5)
            
        Returns:
            Result[List[Dict], NotFoundError]: Success with activity list or Failure
            
        Requirements: 10.1, 10.2, 10.3, 10.4
        """
        try:
            # Verify student exists
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                logger.warning(f"Student not found for recent activity: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Get recent attempts (submitted or graded)
            recent_attempts = self.attempt_repo.get_by_student(student_id).filter(
                Q(status=AttemptStatus.GRADED) | Q(status=AttemptStatus.SUBMITTED)
            ).select_related('exam').order_by('-submitted_at')[:limit]
            
            # Build activity data
            activity_data = []
            for attempt in recent_attempts:
                # Calculate total possible points
                total_possible = sum(q.points for q in attempt.exam.questions.all())
                
                # Calculate percentage if graded
                percentage = None
                if attempt.status == AttemptStatus.GRADED and total_possible > 0:
                    percentage = (float(attempt.total_score) / float(total_possible)) * 100
                
                activity_data.append({
                    'attempt_id': attempt.id,
                    'exam_title': attempt.exam.title,
                    'exam_id': attempt.exam.id,
                    'date': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                    'score': float(attempt.total_score) if attempt.status == AttemptStatus.GRADED else None,
                    'total_possible': float(total_possible),
                    'percentage': round(percentage, 2) if percentage is not None else None,
                    'status': attempt.status
                })
            
            logger.info(f"Recent activity retrieved for student {student_id}: {len(activity_data)} entries")
            return Result.success(activity_data)
            
        except Exception as e:
            logger.error(f"Error retrieving recent activity for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to retrieve recent activity",
                details={'student_id': student_id, 'error': str(e)}
            ))

    def get_exam_history(
        self, 
        student_id: int, 
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[Dict[str, Any]], NotFoundError]:
        """
        Retrieve complete exam history with optional filtering.
        
        Supports filtering by:
        - date_from: Start date for date range filter
        - date_to: End date for date range filter
        - status: Filter by attempt status (graded, submitted)
        
        Args:
            student_id: Student's database ID
            filters: Optional dictionary of filter parameters
            
        Returns:
            Result[List[Dict], NotFoundError]: Success with history list or Failure
            
        Requirements: 6.1, 6.2, 6.3, 6.4, 15.1, 15.2
        """
        try:
            # Verify student exists
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                logger.warning(f"Student not found for exam history: {student_id}")
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Start with all attempts for the student (submitted or graded)
            queryset = self.attempt_repo.get_by_student(student_id).filter(
                Q(status=AttemptStatus.GRADED) | Q(status=AttemptStatus.SUBMITTED)
            ).select_related('exam')
            
            # Apply filters if provided
            if filters:
                # Date range filter
                if 'date_from' in filters and filters['date_from']:
                    try:
                        date_from = filters['date_from']
                        if isinstance(date_from, str):
                            date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                        queryset = queryset.filter(submitted_at__gte=date_from)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date_from filter: {filters['date_from']}")
                
                if 'date_to' in filters and filters['date_to']:
                    try:
                        date_to = filters['date_to']
                        if isinstance(date_to, str):
                            date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                        queryset = queryset.filter(submitted_at__lte=date_to)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid date_to filter: {filters['date_to']}")
                
                # Status filter
                if 'status' in filters and filters['status']:
                    status = filters['status']
                    # Map 'pending' to 'submitted' status
                    if status == 'pending':
                        status = AttemptStatus.SUBMITTED
                    if status in [AttemptStatus.GRADED, AttemptStatus.SUBMITTED]:
                        queryset = queryset.filter(status=status)
            
            # Order by submission date (most recent first)
            queryset = queryset.order_by('-submitted_at')
            
            # Build history data
            history_data = []
            for attempt in queryset:
                # Calculate total possible points
                total_possible = sum(q.points for q in attempt.exam.questions.all())
                
                # Calculate percentage
                percentage = None
                if attempt.status == AttemptStatus.GRADED and total_possible > 0:
                    percentage = (float(attempt.total_score) / float(total_possible)) * 100
                
                history_data.append({
                    'attempt_id': attempt.id,
                    'exam_title': attempt.exam.title,
                    'exam_id': attempt.exam.id,
                    'date': attempt.submitted_at.isoformat() if attempt.submitted_at else None,
                    'score': float(attempt.total_score) if attempt.status == AttemptStatus.GRADED else None,
                    'total_possible': float(total_possible),
                    'percentage': round(percentage, 2) if percentage is not None else None,
                    'status': attempt.status,
                    'is_flagged': attempt.is_flagged,
                    'flag_reason': attempt.flag_reason,
                    'auto_submitted': attempt.auto_submitted
                })
            
            logger.info(f"Exam history retrieved for student {student_id}: {len(history_data)} entries")
            return Result.success(history_data)
            
        except Exception as e:
            logger.error(f"Error retrieving exam history for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to retrieve exam history",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def export_history_csv(self, student_id: int) -> Result[bytes, NotFoundError]:
        """
        Export complete exam history as CSV file.
        
        Generates a CSV file containing all exam records with:
        - Exam name
        - Date taken
        - Score
        - Percentage
        - Status
        - Class information (grade level, strand, section)
        
        Args:
            student_id: Student's database ID
            
        Returns:
            Result[bytes, NotFoundError]: Success with CSV bytes or Failure with error
            
        Requirements: 14.1, 14.2, 14.3, 5.4
        """
        try:
            # Get complete exam history
            history_result = self.get_exam_history(student_id)
            
            if history_result.is_failure():
                return Result.failure(history_result.error)
            
            history_data = history_result.value
            
            # Get student with class information (Requirement 5.4)
            student = self.student_repo.get_by_id(student_id)
            if student is None:
                return Result.failure(NotFoundError(
                    message=f"Student with ID {student_id} not found",
                    details={'student_id': student_id}
                ))
            
            # Extract class information, handling null class assignments
            grade_level = ''
            strand = ''
            section = ''
            if student.class_assigned:
                grade_level = student.class_assigned.grade_level
                strand = student.class_assigned.strand
                section = student.class_assigned.section
            
            # Create CSV in memory
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header with class columns (Requirement 5.4)
            writer.writerow([
                'Exam Title',
                'Date Taken',
                'Score',
                'Total Possible',
                'Percentage',
                'Status',
                'Grade Level',
                'Strand',
                'Section'
            ])
            
            # Write data rows
            for entry in history_data:
                # Format date
                date_str = ''
                if entry['date']:
                    try:
                        date_obj = datetime.fromisoformat(entry['date'].replace('Z', '+00:00'))
                        date_str = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                    except (ValueError, AttributeError):
                        date_str = entry['date']
                
                # Format score
                score_str = f"{entry['score']:.2f}" if entry['score'] is not None else 'Pending'
                
                # Format percentage
                percentage_str = f"{entry['percentage']:.2f}%" if entry['percentage'] is not None else 'Pending'
                
                # Format status
                status_str = 'Graded' if entry['status'] == AttemptStatus.GRADED else 'Pending'
                
                writer.writerow([
                    entry['exam_title'],
                    date_str,
                    score_str,
                    f"{entry['total_possible']:.2f}",
                    percentage_str,
                    status_str,
                    grade_level,
                    strand,
                    section
                ])
            
            # Get CSV content as bytes
            csv_content = output.getvalue().encode('utf-8')
            output.close()
            
            logger.info(f"CSV export generated for student {student_id}: {len(history_data)} entries")
            return Result.success(csv_content)
            
        except Exception as e:
            logger.error(f"Error exporting history CSV for student {student_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to export exam history",
                details={'student_id': student_id, 'error': str(e)}
            ))
    
    def get_statistics_by_class(self, class_id: int) -> Result[Dict[str, Any], NotFoundError]:
        """
        Calculate statistics for a specific class.
        
        Computes:
        - Average score for students in the class
        - Number of students in the class
        - Total number of attempts by class students
        - Class name information
        
        Args:
            class_id: Class database ID
            
        Returns:
            Result[Dict, NotFoundError]: Success with statistics dict or Failure with error
            
        Requirements: 5.2, 5.3
        """
        try:
            # Import Class model
            from users.models import Class
            
            # Verify class exists
            try:
                cls = Class.objects.select_related('teacher').get(id=class_id)
            except Class.DoesNotExist:
                logger.warning(f"Class not found for statistics: {class_id}")
                return Result.failure(NotFoundError(
                    message=f"Class with ID {class_id} not found",
                    details={'class_id': class_id}
                ))
            
            # Get all students in this class
            from users.models import Student
            students_in_class = Student.objects.filter(class_assigned_id=class_id)
            student_count = students_in_class.count()
            
            if student_count == 0:
                # Return empty statistics for classes with no students
                statistics = {
                    'class_id': class_id,
                    'class_name': str(cls),
                    'grade_level': cls.grade_level,
                    'strand': cls.strand,
                    'section': cls.section,
                    'student_count': 0,
                    'total_attempts': 0,
                    'average': 0.0,
                    'highest': 0.0,
                    'lowest': 0.0
                }
                logger.info(f"No students found in class {class_id}")
                return Result.success(statistics)
            
            # Get all graded attempts for students in this class (Requirement 5.2)
            student_ids = list(students_in_class.values_list('id', flat=True))
            graded_attempts = Attempt.objects.filter(
                student_id__in=student_ids,
                status=AttemptStatus.GRADED
            ).select_related('exam').prefetch_related('exam__questions')
            
            total_attempts = graded_attempts.count()
            
            if total_attempts == 0:
                # Return statistics with no attempts
                statistics = {
                    'class_id': class_id,
                    'class_name': str(cls),
                    'grade_level': cls.grade_level,
                    'strand': cls.strand,
                    'section': cls.section,
                    'student_count': student_count,
                    'total_attempts': 0,
                    'average': 0.0,
                    'highest': 0.0,
                    'lowest': 0.0
                }
                logger.info(f"No graded attempts found for class {class_id}")
                return Result.success(statistics)
            
            # Calculate average score (Requirement 5.3)
            stats = graded_attempts.aggregate(
                average=Avg('total_score'),
                highest=Max('total_score'),
                lowest=Min('total_score')
            )
            
            statistics = {
                'class_id': class_id,
                'class_name': str(cls),
                'grade_level': cls.grade_level,
                'strand': cls.strand,
                'section': cls.section,
                'student_count': student_count,
                'total_attempts': total_attempts,
                'average': round(float(stats['average'] or 0), 2),
                'highest': float(stats['highest'] or 0),
                'lowest': float(stats['lowest'] or 0)
            }
            
            logger.info(f"Statistics calculated for class {class_id}: {statistics}")
            return Result.success(statistics)
            
        except Exception as e:
            logger.error(f"Error calculating statistics for class {class_id}: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to calculate class statistics",
                details={'class_id': class_id, 'error': str(e)}
            ))

    def get_passing_rate_by_subject_per_section(self, teacher_id: Optional[int] = None) -> Result[Dict[str, Any], NotFoundError]:
        """
        Calculate passing rate for each subject grouped by class section.
        
        Returns passing rates (percentage of students scoring >= 60%) for each subject
        within each class section. Useful for identifying which subjects/sections need attention.
        
        Args:
            teacher_id: Optional teacher ID to filter classes by teacher
            
        Returns:
            Result[Dict, NotFoundError]: Success with passing rate data or Failure with error
            
        Format:
        {
            'sections': ['Grade 11 - HUMSS - A', 'Grade 11 - GAS - B', ...],
            'subjects': ['English', 'Math', 'Science', ...],
            'data': {
                'English': [75.5, 82.3, ...],  # passing rates per section
                'Math': [65.2, 70.1, ...],
                ...
            }
        }
        """
        try:
            from users.models import Class, Student
            from exams.models import Exam
            
            # Get classes (optionally filtered by teacher)
            classes_query = Class.objects.all().order_by('grade_level', 'strand', 'section')
            if teacher_id:
                classes_query = classes_query.filter(teacher_id=teacher_id)
            
            classes = list(classes_query)
            
            if not classes:
                logger.info("No classes found for passing rate calculation")
                return Result.success({
                    'sections': [],
                    'subjects': [],
                    'data': {}
                })
            
            # Get all subjects from exams
            subjects = list(Exam.objects.values_list('subject', flat=True).distinct().exclude(subject__isnull=True).exclude(subject=''))
            
            if not subjects:
                logger.info("No subjects found for passing rate calculation")
                return Result.success({
                    'sections': [str(cls) for cls in classes],
                    'subjects': [],
                    'data': {}
                })
            
            # Build section labels
            section_labels = [str(cls) for cls in classes]
            
            # Calculate passing rates for each subject per section
            passing_rate_data = {}
            
            for subject in subjects:
                subject_rates = []
                
                for cls in classes:
                    # Get students in this class
                    student_ids = list(Student.objects.filter(class_assigned=cls).values_list('id', flat=True))
                    
                    if not student_ids:
                        # No students in class
                        subject_rates.append(0.0)
                        continue
                    
                    # Get graded attempts for this subject and these students
                    subject_attempts = Attempt.objects.filter(
                        student_id__in=student_ids,
                        status=AttemptStatus.GRADED,
                        exam__subject=subject
                    ).select_related('exam').prefetch_related('exam__questions')
                    
                    if not subject_attempts.exists():
                        # No attempts for this subject in this class
                        subject_rates.append(0.0)
                        continue
                    
                    # Calculate passing rate (60% threshold)
                    passed_count = 0
                    total_count = subject_attempts.count()
                    
                    for attempt in subject_attempts:
                        # Calculate total possible points
                        total_possible = sum(float(q.points) for q in attempt.exam.questions.all())
                        
                        if total_possible > 0:
                            percentage = (float(attempt.total_score) / total_possible) * 100
                            if percentage >= 60.0:
                                passed_count += 1
                    
                    # Calculate passing rate percentage
                    passing_rate = (passed_count / total_count * 100) if total_count > 0 else 0.0
                    subject_rates.append(round(passing_rate, 2))
                
                passing_rate_data[subject] = subject_rates
            
            result = {
                'sections': section_labels,
                'subjects': subjects,
                'data': passing_rate_data
            }
            
            logger.info(f"Passing rate by subject per section calculated: {len(subjects)} subjects, {len(classes)} sections")
            return Result.success(result)
            
        except Exception as e:
            logger.error(f"Error calculating passing rate by subject per section: {str(e)}")
            return Result.failure(NotFoundError(
                message="Failed to calculate passing rate by subject per section",
                details={'error': str(e)}
            ))
