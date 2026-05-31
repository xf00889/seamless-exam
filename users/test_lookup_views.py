import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from users.models import Teacher, Quarter


class QuarterLookupViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='teacher_lookup',
            password='testpass123',
            first_name='Lookup',
            last_name='Teacher',
        )
        self.teacher = Teacher.objects.create(user=self.user, department='Science')
        self.client.force_login(self.user)
        session = self.client.session
        session['user_type'] = 'teacher'
        session.save()

    def test_create_quarter_view_creates_quarter(self):
        response = self.client.post(
            reverse('create_quarter'),
            data=json.dumps({'name': '1st Quarter'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Quarter.objects.filter(name='1st Quarter').exists())

    def test_update_quarter_view_renames_quarter(self):
        quarter = Quarter.objects.create(name='1st Quarter')

        response = self.client.post(
            reverse('update_quarter'),
            data=json.dumps({'id': quarter.id, 'name': 'Quarter 1'}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        quarter.refresh_from_db()
        self.assertEqual(quarter.name, 'Quarter 1')
