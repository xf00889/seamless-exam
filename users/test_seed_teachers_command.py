import json
import os
import tempfile

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from users.models import Teacher


class SeedTeachersCommandTests(TestCase):
    def test_seeds_single_teacher_from_cli_args(self):
        call_command(
            "seed_teachers",
            "--username",
            "teacher_seed",
            "--password",
            "secret123",
            "--first-name",
            "Seed",
            "--last-name",
            "Teacher",
            "--department",
            "Math",
            "--staff",
        )

        user = User.objects.get(username="teacher_seed")
        teacher = Teacher.objects.get(user=user)

        self.assertEqual(user.first_name, "Seed")
        self.assertEqual(user.last_name, "Teacher")
        self.assertTrue(user.is_staff)
        self.assertEqual(teacher.department, "Math")

    def test_skips_existing_user_without_reset(self):
        user = User.objects.create_user(username="teacher_seed", password="oldpass")
        Teacher.objects.create(user=user, department="Old Dept")

        call_command(
            "seed_teachers",
            "--username",
            "teacher_seed",
            "--password",
            "newpass123",
            "--department",
            "New Dept",
        )

        user.refresh_from_db()
        teacher = Teacher.objects.get(user=user)

        self.assertTrue(user.check_password("oldpass"))
        self.assertEqual(teacher.department, "Old Dept")

    def test_resets_existing_user_when_reset_flag_is_used(self):
        user = User.objects.create_user(username="teacher_seed", password="oldpass")
        Teacher.objects.create(user=user, department="Old Dept")

        call_command(
            "seed_teachers",
            "--username",
            "teacher_seed",
            "--password",
            "newpass123",
            "--department",
            "New Dept",
            "--reset",
        )

        user.refresh_from_db()
        teacher = Teacher.objects.get(user=user)

        self.assertTrue(user.check_password("newpass123"))
        self.assertEqual(teacher.department, "New Dept")

    def test_seeds_multiple_teachers_from_json_file(self):
        payload = [
            {
                "username": "teacher_a",
                "password": "pass1234",
                "first_name": "A",
                "last_name": "Teacher",
                "department": "Science",
                "is_staff": True,
            },
            {
                "username": "teacher_b",
                "password": "pass5678",
                "first_name": "B",
                "last_name": "Teacher",
                "department": "English",
            },
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as temp_file:
            temp_file.write(json.dumps(payload))
            temp_file_path = temp_file.name

        try:
            call_command("seed_teachers", "--file", temp_file_path)
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        self.assertTrue(User.objects.filter(username="teacher_a").exists())
        self.assertTrue(User.objects.filter(username="teacher_b").exists())
        self.assertEqual(Teacher.objects.count(), 2)
