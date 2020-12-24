from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=128)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(User,
                               related_name='posts_created',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)
    class Meta:
        # most recent posts at the top
        ordering = ['-created']

    def __str__(self):
        return str(self.title)

class Comment(models.Model):
    post = models.ForeignKey('Post', related_name='comments',
                             on_delete=models.CASCADE)
    parent = models.ForeignKey('Comment',on_delete=models.CASCADE,
                               null=True, blank=True,
                               related_name='children')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    author = models.ForeignKey(User,
                               related_name='comments_added',
                               on_delete=models.CASCADE,
                               blank=True,
                               null=True)

    class Meta:
        # oldest comments at the top
        ordering = ['created']

    def __str__(self):
        return str(self.text[0:50]) + '...'