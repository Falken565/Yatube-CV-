from django import forms
from django.forms.widgets import Textarea

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст сообщения'),
            'group': ('Группа'),
            'image': ('Изображение')
        }
        help_texts = {
            'text': ('Тут можно оставить послание для потомков'),
            'group': ('Кошечки, собачки... выбирай, что нравится'),
            'image': ('Добавить изображение')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': Textarea}
        labels = {'text': 'Текст комментария'}
