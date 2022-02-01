import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Group, Post

User = get_user_model()


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostCreateFormTests(TestCase):
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
            content=PostCreateFormTests.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='тестовая группа ура-ура'
        )
        cls.form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
            'image': PostCreateFormTests.uploaded,
        }
        cls.form = PostForm()
        cls.tasks_count = Post.objects.count()

        cls.guest_client = Client()
        cls.user = User.objects.create(username='tester')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        return super().tearDownClass()

    def test_create_post(self):
        """Create post authorized user test"""
        response = self.authorized_client.post(
            reverse('new_post'),
            data=PostCreateFormTests.form_data,
            follow=True
        )
        test_text = PostCreateFormTests.form_data['text']
        test_image = f'posts/{PostCreateFormTests.uploaded}'
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(
            Post.objects.count(),
            PostCreateFormTests.tasks_count + 1
        )
        self.assertTrue(
            Post.objects.filter(
                text=test_text,
                group=PostCreateFormTests.group,
                author=PostCreateFormTests.user,
                image=test_image,
            ).exists()
        )

    def test_create_post_guest(self):
        """Create post guest user test"""
        login_url = reverse('login')
        new_url = reverse('new_post')
        self.redirect_url = f'{login_url}?next={new_url}'
        response = self.guest_client.post(
            reverse('new_post'),
            data=PostCreateFormTests.form_data,
            follow=True
        )
        self.assertRedirects(response, self.redirect_url)
        self.assertEqual(
            Post.objects.count(),
            PostCreateFormTests.tasks_count
        )


class PostEditFormTest(TestCase):
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
            group=PostEditFormTest.group,
            author=User.objects.create(username='tester')
        )
        cls.guest_client = Client()
        cls.user = PostEditFormTest.post.author
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.form = PostForm()
        cls.count_group = Post.objects.filter(
            group=PostEditFormTest.group
        ).count()

    def test_edit_post(self):
        form_data = {
            'text': 'Отредактированно!',
            'group': '',
        }
        response = self.authorized_client.post(
            reverse('edit', kwargs={
                'username': self.user.username,
                'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={
                'username': self.user.username,
                'post_id': self.post.id})
        )
        self.assertTrue(
            Post.objects.filter(
                text='Отредактированно!',
            ).exists()
        )
        self.assertEqual(
            Post.objects.filter(
                group=PostEditFormTest.group
            ).count(),
            PostEditFormTest.count_group - 1
        )


class CommentFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый текст номер раз',
            author=User.objects.create(username='test_author'),
            group=Group.objects.create(
                title='test group',
                slug='test-slug',
                description='тестовая группа'),
        )
        cls.guest_client = Client()
        cls.user = User.objects.create(username='Tester')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.form = CommentForm()

    def test_comment_authorized_user(self):
        form_data = {
            'text': 'Новый комментарий!',
        }
        response = self.authorized_client.post(
            reverse('add_comment', kwargs={
                'username': CommentFormTest.post.author.username,
                'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={
                'username': CommentFormTest.post.author.username,
                'post_id': self.post.id})
        )
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text']
            ).exists
        )

    def test_comment_guest_user(self):
        form_data = {
            'text': 'еще один Новый комментарий!',
        }
        login_url = reverse('login')
        post_url = reverse('add_comment', kwargs={
            'username': CommentFormTest.post.author.username,
            'post_id': self.post.id}
        )
        redirect_url = f'{login_url}?next={post_url}'
        response = self.guest_client.post(
            reverse('add_comment', kwargs={
                'username': CommentFormTest.post.author.username,
                'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        comment_exist = Comment.objects.filter(
            text=form_data['text']
        ).exists()
        self.assertRedirects(response, redirect_url)
        self.assertEqual(comment_exist, False)
