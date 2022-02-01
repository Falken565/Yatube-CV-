import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class ViewsModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=ViewsModelTest.small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='тестовая группа ура-ура'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст и еще чутка текста',
            group=ViewsModelTest.group,
            author=User.objects.create(username='tester'),
            image=ViewsModelTest.uploaded
        )
        cls.templates_pages = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html':
                reverse('group', kwargs={'slug': ViewsModelTest.group.slug}
                        ),
        }
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = ViewsModelTest.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """Correct template test."""
        for template, reverse_name in ViewsModelTest.templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Correct context for index page test."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        author_0 = first_object.author.username
        date_0 = first_object.pub_date
        text_0 = first_object.text
        image_0 = first_object.image
        self.assertEqual(author_0, self.post.author.username)
        self.assertEqual(date_0, self.post.pub_date)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(image_0, self.post.image)

    def test_group_pages_show_correct_context(self):
        """Correct context for group page test."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug})
        )
        first_group_object = response.context['page'][0]
        image_0 = first_group_object.image
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(
            response.context['group'].description, self.group.description)
        self.assertEqual(response.context['group'].slug, self.group.slug)
        self.assertEqual(image_0, self.post.image)

    def test_new_page_shows_correct_context(self):
        """Correct contest for new post page test."""
        response = self.authorized_client.get(reverse('new_post'))
        for value, expected in ViewsModelTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_page_shows_correct_context(self):
        """Correct contest for profile page test."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': self.user.username})
        )
        first_object = response.context['page'][0]
        username_0 = first_object.author.username
        date_0 = first_object.pub_date
        text_0 = first_object.text
        count = Post.objects.count()
        image_0 = first_object.image
        self.assertEqual(username_0, self.post.author.username)
        self.assertEqual(date_0, self.post.pub_date)
        self.assertEqual(text_0, self.post.text)
        self.assertEqual(image_0, self.post.image)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['username'], self.user.username)
        self.assertEqual(response.context['count_posts'], count)

    def test_post_page_shows_correct_context(self):
        """Correct contest for post page test."""
        response = self.authorized_client.get(
            reverse('post', kwargs={
                'username': self.user.username,
                'post_id': self.post.id}
            )
        )
        text = response.context['post'].text
        date = response.context['post'].pub_date
        username = response.context['post'].author.username
        post_id = response.context['post'].pk
        image = response.context['post'].image
        count = Post.objects.count()
        self.assertEqual(username, self.post.author.username)
        self.assertEqual(date, self.post.pub_date)
        self.assertEqual(text, self.post.text)
        self.assertEqual(post_id, self.post.id)
        self.assertEqual(image, self.post.image)
        self.assertEqual(response.context['author'], self.user)
        self.assertEqual(response.context['username'], self.user.username)
        self.assertEqual(response.context['count_posts'], count)

    def test_edit_page_shows_correct_context(self):
        """Correct contest for edit post page test."""
        response = self.authorized_client.get(
            reverse('edit', kwargs={
                'username': self.user.username,
                'post_id': self.post.id}
            )
        )
        self.assertEqual(response.context['post_id'], self.post.id)
        self.assertEqual(response.context['username'], self.user.username)
        for value, expected in ViewsModelTest.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_cache(self):
        """Index page cache test."""
        response = self.authorized_client.get(reverse('index'))
        len_one = len(response.content)
        Post.objects.create(
            text='Тестовый текст',
            author=ViewsModelTest.post.author,
            group=ViewsModelTest.post.group,
        )
        response = self.authorized_client.get(reverse('index'))
        len_two = len(response.content)
        self.assertEqual(len_one, len_two)


class GroupPostViewTest(TestCase):
    """Correct group post view test."""
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
            group=GroupPostViewTest.group,
            author=User.objects.create(username='tester')
        )
        cls.post_no_gr = Post.objects.create(
            text='Тестовый текст и еще чутка текста',
            author=GroupPostViewTest.post.author
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = GroupPostViewTest.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.count_all = Post.objects.count()
        self.count_group = Post.objects.filter(
            group=GroupPostViewTest.group
        ).count()

    def test_index_page_post_amount(self):
        """Correct number of posts on index page test."""
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page')), self.count_all)

    def test_group_page_post_amount(self):
        """Correct number of posts on group page test."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug}))
        self.assertEqual(len(response.context.get('page')), self.count_group)

    def test_group_page_shows_correct_context(self):
        """Correct contest for group post on group page test."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.group.slug}))
        first_object = response.context['page'][0]
        title_0 = first_object.group.title
        slug_0 = first_object.group.slug
        description_0 = first_object.group.description
        self.assertEqual(title_0, self.group.title)
        self.assertEqual(slug_0, self.group.slug)
        self.assertEqual(description_0, self.group.description)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст номер раз',
            author=User.objects.create(username='tester'),
            group=Group.objects.create(
                title='test group',
                slug='test-slug',
                description='тестовая группа ура-ура'),
        )
        for i in range(1, 13):
            cls.post = Post.objects.create(
                text='Тестовый текст',
                author=PaginatorViewsTest.post.author,
                group=PaginatorViewsTest.post.group,
            )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = PaginatorViewsTest.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_index_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page')), 10)

    def test_first_group_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.post.group.slug})
        )
        self.assertEqual(len(response.context.get('page')), 10)

    def test_second_index_page_contains_three_records(self):
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page')), 3)

    def test_second_group_page_contains_three_records(self):
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': self.post.group.slug}) + '?page=2'
        )
        self.assertEqual(len(response.context.get('page')), 3)


class FollowViewTest(TestCase):
    """Correct group post view test."""
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
            group=FollowViewTest.group,
            author=User.objects.create(username='test_author')
        )
        cls.count = FollowViewTest.post.author.following.count()

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create(username='test_follower')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        Follow.objects.create(
            user=self.user,
            author=FollowViewTest.post.author
        )

    def test_followed(self):
        """Authorized user followed test"""
        FollowViewTest.count_2 = FollowViewTest.post.author.following.count()
        self.assertEqual(FollowViewTest.count, FollowViewTest.count_2 - 1)

    def test_unfollowed(self):
        """Authorized user unfollowed test"""
        Follow.objects.filter(
            user=self.user,
            author=FollowViewTest.post.author
        ).delete()
        FollowViewTest.count_3 = FollowViewTest.post.author.following.count()
        self.assertEqual(FollowViewTest.count, FollowViewTest.count_3)

    def test_follow_page_following_user(self):
        """Correct post view on follow page following user test"""
        response = self.authorized_client.get(
            reverse('follow_index')
        )
        self.assertEqual(len(response.context.get('page')), 1)

    def test_follow_page_not_following_user(self):
        """Correct post view on follow page not following user test"""
        cache.clear()
        self.guest_client = Client()
        self.user_2 = User.objects.create(username='test_not_follower')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_2)
        response = self.authorized_client.get(
            reverse('follow_index')
        )
        self.assertEqual(len(response.context.get('page')), 0)
