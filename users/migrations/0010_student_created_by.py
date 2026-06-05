from django.db import migrations, models


def backfill_student_created_by(apps, schema_editor):
    """
    Backfill Student.created_by from the owning class's teacher for any
    student that is currently assigned to a class. Students without a
    class assignment are left with NULL created_by (superadmin-only).
    """
    Student = apps.get_model('users', 'Student')
    Class = apps.get_model('users', 'Class')
    Teacher = apps.get_model('users', 'Teacher')

    students_with_class = (
        Student.objects
        .filter(class_assigned__isnull=False, created_by__isnull=True)
        .select_related('class_assigned', 'class_assigned__teacher')
    )
    for student in students_with_class:
        student.created_by_id = student.class_assigned.teacher_id
        student.save(update_fields=['created_by'])


def reverse_backfill(apps, schema_editor):
    """No-op: we don't un-fill created_by on rollback (it's informational)."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0009_systemsettings_maintenance_message_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='created_by',
            field=models.ForeignKey(
                blank=True,
                db_index=True,
                help_text='Teacher who created this student account. '
                          'Used to scope account visibility to the owning teacher.',
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name='created_students',
                to='users.teacher',
            ),
        ),
        migrations.RunPython(backfill_student_created_by, reverse_backfill),
    ]
