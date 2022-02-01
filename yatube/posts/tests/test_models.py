from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test group',
            slug='test',
            description='тестовая группа ура-ура'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст и еще чутка текста',
            group=cls.group,
            author=User.objects.create(username='tester')
        )

    def test_str_method_post(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_str_method_group(self):
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
