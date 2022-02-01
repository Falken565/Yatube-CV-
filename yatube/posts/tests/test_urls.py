from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class UrlsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='тестовая группа ура-ура'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст и еще чутка текста',
            group=cls.group,
            author=User.objects.create(username='tester')
        )
        cls.templates_url_names = {
            'index.html': '/',
            'group.html': '/group/test-slug/',
            'new.html': '/new/',
            'profile.html': '/tester/',
            'post.html': '/tester/1/',
        }

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = UrlsModelTest.post.author
        self.user_2 = User.objects.create_user(username='stranger')
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_2)
        self.edit_url = '/tester/1/edit/'
        self.new_url = '/new/'
        self.post_url = '/tester/1/'
        self.redirect_new_url = '/auth/login/?next=/new/'
        self.redirect_edit_url = '/auth/login/?next=/tester/1/edit/'
        self.broken_url = '/tester/15/'

    def test_pages(self):
        """Pages access test."""
        for template, adress in UrlsModelTest.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """Correct template test."""
        for template, adress in UrlsModelTest.templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_edit_page(self):
        response = self.authorized_client.get(self.edit_url)
        self.assertTemplateUsed(response, 'new.html')

    def test_new_page_anonymous(self):
        """Access denied for creation new post by anonymous test."""
        response = self.guest_client.get(self.new_url)
        self.assertEqual(response.status_code, 302)

    def test_new_page_redirect_anonymous_on_auth_login(self):
        """Redirect for anonymous attempt creation new post test."""
        response = self.guest_client.get(self.new_url, follow=True)
        self.assertRedirects(
            response, self.redirect_new_url)

    def test_post_edit_page_anonymous(self):
        """Access denied for edit post by anonymous test."""
        response = self.guest_client.get(self.edit_url)
        self.assertEqual(response.status_code, 302)

    def test_post_edit_page_not_author(self):
        """Access denied for edit post not by author test."""
        response = self.authorized_client_2.get(self.edit_url)
        self.assertEqual(response.status_code, 302)

    def test_post_edit_page_author(self):
        """Access for edit post by post author test."""
        response = self.authorized_client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_page_redirect_anonymous_on_auth_login(self):
        """Redirect for anonymous attempt for edit post test."""
        response = self.guest_client.get(self.edit_url, follow=True)
        self.assertRedirects(
            response, self.redirect_edit_url)

    def test_edit_page_redirect_not_author(self):
        """Redirect for not author attempt for edit post test."""
        response = self.authorized_client_2.get(self.edit_url, follow=True)
        self.assertRedirects(
            response, self.post_url)

    def test_404(self):
        """Pages 404 test."""
        response = self.authorized_client.get(self.broken_url)
        self.assertEqual(response.status_code, 404)
