from pathlib import Path

from django.test import SimpleTestCase


class GlobalFontTests(SimpleTestCase):
    base_dir = Path(__file__).resolve().parent.parent

    def read_text(self, relative_path):
        return (self.base_dir / relative_path).read_text(encoding="utf-8")

    def test_space_grotesk_is_self_hosted_and_used_globally(self):
        css = self.read_text("static/css/main.css")
        font_dir = self.base_dir / "static/fonts/space-grotesk"

        self.assertTrue(font_dir.exists())
        self.assertTrue(
            (font_dir / "space-grotesk-latin-400-normal.woff2").exists()
        )
        self.assertIn("font-family: 'Space Grotesk'", css)
        self.assertIn("url('../fonts/space-grotesk/", css)
        self.assertIn("--font-sans: 'Space Grotesk'", css)
        self.assertIn("font-family: var(--font-sans);", css)
        self.assertIn("code,", css)
        self.assertIn("samp", css)
        self.assertIn(".swal2-popup", css)

    def test_templates_do_not_load_runtime_google_fonts(self):
        templates = [
            "templates/home.html",
            "templates/users/student_login.html",
            "templates/users/teacher_login.html",
        ]

        for template in templates:
            with self.subTest(template=template):
                html = self.read_text(template)
                self.assertNotIn("fonts.googleapis.com", html)
                self.assertNotIn("fonts.gstatic.com", html)

    def test_page_styles_do_not_override_global_font_with_previous_fonts(self):
        files = [
            "static/css/components/forms.css",
            "static/css/pages/home.css",
            "static/css/pages/login.css",
            "static/css/pages/auth-landing.css",
            "static/js/pages/dashboard-charts.js",
            "theme/static_src/tailwind.config.js",
        ]

        for file_path in files:
            with self.subTest(file_path=file_path):
                content = self.read_text(file_path)
                self.assertNotIn("@import url(", content)
                self.assertNotIn("'Inter'", content)
                self.assertNotIn("'Merriweather'", content)
                self.assertNotIn('"Manrope"', content)
                self.assertNotIn('"Parisienne"', content)
                self.assertNotIn('"Playfair Display"', content)
                self.assertNotIn("monospace", content)
