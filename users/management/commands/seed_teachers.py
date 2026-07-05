"""
Management command to seed teacher login accounts.

Examples:
    python manage.py seed_teachers --username teacher1 --password pass123
    python manage.py seed_teachers --file data/teachers.json
    python manage.py seed_teachers --file data/teachers.json --reset
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from users.models import School, Teacher


class Command(BaseCommand):
    help = "Seed teacher accounts from CLI arguments or a JSON file"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--username",
            type=str,
            help="Teacher username (single-account mode)",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Teacher password (single-account mode)",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="",
            help="Teacher email (single-account mode)",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="",
            help="Teacher first name (single-account mode)",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="",
            help="Teacher last name (single-account mode)",
        )
        parser.add_argument(
            "--department",
            type=str,
            default="",
            help="Teacher department (single-account mode)",
        )
        parser.add_argument(
            "--file",
            type=str,
            help="Path to JSON file containing teacher entries (array of objects)",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="If username exists, overwrite that teacher account details",
        )
        parser.add_argument(
            "--superuser",
            action="store_true",
            help="Create seeded users as superusers in single-account mode",
        )
        parser.add_argument(
            "--staff",
            action="store_true",
            help="Create seeded users as staff in single-account mode",
        )
        parser.add_argument(
            "--school-id",
            type=int,
            default=None,
            help="ID of the school to associate teachers with (required if multiple schools exist)",
        )

    def handle(self, *args, **options) -> None:
        teachers_payload = self._build_payload(options)
        reset = options.get("reset", False)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        school_id = options.get("school_id")
        school = None
        if school_id:
            try:
                school = School.objects.get(id=school_id)
            except School.DoesNotExist:
                raise CommandError(f"School with id={school_id} does not exist.")
        else:
            school = School.objects.first()
            if not school:
                raise CommandError(
                    "No schools exist. Create a school first or specify --school-id."
                )

        for teacher_data in teachers_payload:
            username = teacher_data["username"]
            with transaction.atomic():
                user = User.objects.filter(username=username).first()
                if user and not reset:
                    skipped_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'Skipped existing teacher "{username}"')
                    )
                    continue

                if user and reset:
                    user.email = teacher_data.get("email", "")
                    user.first_name = teacher_data.get("first_name", "")
                    user.last_name = teacher_data.get("last_name", "")
                    user.is_staff = teacher_data.get("is_staff", False)
                    user.is_superuser = teacher_data.get("is_superuser", False)
                    user.set_password(teacher_data["password"])
                    user.save()

                    teacher, _ = Teacher.objects.get_or_create(user=user)
                    teacher.school = school
                    teacher.department = teacher_data.get("department") or ""
                    teacher.save()
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f'Updated teacher "{username}"'))
                    continue

                user = User.objects.create_user(
                    username=username,
                    password=teacher_data["password"],
                    email=teacher_data.get("email", ""),
                    first_name=teacher_data.get("first_name", ""),
                    last_name=teacher_data.get("last_name", ""),
                    is_staff=teacher_data.get("is_staff", False),
                    is_superuser=teacher_data.get("is_superuser", False),
                )
                Teacher.objects.create(
                    user=user,
                    school=school,
                    department=teacher_data.get("department") or "",
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created teacher "{username}"'))

        self.stdout.write(
            self.style.WARNING(
                f"Done. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
            )
        )

    def _build_payload(self, options: dict[str, Any]) -> list[dict[str, Any]]:
        file_path = options.get("file")
        if file_path:
            return self._load_from_file(file_path)

        username = (options.get("username") or "").strip()
        password = options.get("password") or ""
        if not username or not password:
            raise CommandError(
                "Provide --username and --password, or use --file with teacher data."
            )

        return [
            {
                "username": username,
                "password": password,
                "email": (options.get("email") or "").strip(),
                "first_name": (options.get("first_name") or "").strip(),
                "last_name": (options.get("last_name") or "").strip(),
                "department": (options.get("department") or "").strip(),
                "is_staff": bool(options.get("staff")),
                "is_superuser": bool(options.get("superuser")),
            }
        ]

    def _load_from_file(self, raw_path: str) -> list[dict[str, Any]]:
        file_path = Path(raw_path)
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid JSON in {file_path}: {exc}") from exc

        if not isinstance(data, list):
            raise CommandError("JSON file must contain an array of teacher objects.")

        payload: list[dict[str, Any]] = []
        for index, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                raise CommandError(f"Entry #{index} must be a JSON object.")

            username = str(item.get("username", "")).strip()
            password = str(item.get("password", ""))
            if not username or not password:
                raise CommandError(
                    f'Entry #{index} must include non-empty "username" and "password".'
                )

            payload.append(
                {
                    "username": username,
                    "password": password,
                    "email": str(item.get("email", "")).strip(),
                    "first_name": str(item.get("first_name", "")).strip(),
                    "last_name": str(item.get("last_name", "")).strip(),
                    "department": str(item.get("department", "")).strip(),
                    "is_staff": bool(item.get("is_staff", False)),
                    "is_superuser": bool(item.get("is_superuser", False)),
                }
            )

        return payload
