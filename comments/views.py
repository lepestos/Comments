from django.shortcuts import render, get_object_or_404, redirect
from django.views import generic
from .models import *

class PostListView(generic.ListView):
    model = Post
    context_object_name = 'posts'

class PostDetailView(generic.DetailView):
    model = Post
    def post(self, request, pk):
        _post = get_object_or_404(Post, id=pk)
        text = request.POST['text']
        comment = Comment.objects.create(post=_post, text=text)
        return redirect('post-detail', pk=pk)
