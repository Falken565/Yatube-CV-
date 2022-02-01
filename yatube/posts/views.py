from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    main = True
    return render(
        request,
        'index.html',
        {'page': page, 'index': main}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.groups.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'page': page, 'group': group}
    )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    count_posts = post_list.count()
    count_following = author.follower.count()
    count_followers = author.following.count()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    user = request.user
    if user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        ).exists()
        return render(
            request,
            'profile.html',
            {'page': page, 'author': author,
             'count_posts': count_posts, 'username': username,
             'following': following, 'count_following': count_following,
             'count_followers': count_followers}
        )
    return render(
        request,
        'profile.html',
        {'page': page, 'author': author,
         'count_posts': count_posts, 'username': username,
         'count_following': count_following,
         'count_followers': count_followers}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    author = post.author
    count_posts = author.posts.all().count()
    count_following = author.follower.count()
    count_followers = author.following.count()
    comments = Comment.objects.filter(post=post)
    form = CommentForm()
    return render(
        request,
        'post.html',
        {'post': post, 'author': author, 'count_posts': count_posts,
         'post_id': post_id, 'username': username,
         'comments': comments, 'form': form,
         'count_following': count_following,
         'count_followers': count_followers}
    )


@login_required
def new_post(request):
    header = 'Добавить запись'
    card_header = 'Новая запись'
    action = 'Добавить'
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')
    return render(
        request,
        'new.html',
        {'form': form, 'header': header,
         'action': action, 'card_header': card_header}
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    user = request.user
    if not author.username == user.username:
        return redirect('post', username=username, post_id=post_id)
    header = 'Редактировать запись'
    card_header = 'Редактируемая запись'
    action = 'Сохранить'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        mid_post = form.save(commit=False)
        mid_post.author = request.user
        mid_post.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request,
        'new.html',
        {'post': post, 'form': form, 'header': header, 'action': action,
         'post_id': post_id, 'username': username,
         'card_header': card_header}
    )


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None,)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect(reverse('post', args=[username, post_id]))
    return redirect(reverse('post', args=[username, post_id]))


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follow = True
    return render(
        request,
        'follow.html',
        {'page': page, 'follow': follow}
    )


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if not Follow.objects.filter(
        user=user,
        author=author
    ).exists() and user != author:
        Follow.objects.create(user=user, author=author)
    return redirect('profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    follow = Follow.objects.filter(
        user=user,
        author=author
    )
    if follow.exists() and user != author:
        follow.delete()
    return redirect('profile', username)


@login_required
def post_delete(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = post.author
    user = request.user
    if not author.username == user.username:
        return redirect('post', username=username, post_id=post_id)
    post.delete()
    return redirect('index')
