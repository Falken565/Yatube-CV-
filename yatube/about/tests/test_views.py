from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.templates_url_names = {
            'about/author.html': 'about:author',
            'about/tech.html': 'about:tech',
        }

    def test_pages_accessible_by_name(self):
        for template, urls in self.templates_url_names.items():
            with self.subTest(urls=urls):
                response = self.guest_client.get(reverse(urls))
                self.assertEqual(response.status_code, 200)

    def test_pages_use_correct_template(self):
        for template, url in self.templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url))
                self.assertTemplateUsed(response, template)
