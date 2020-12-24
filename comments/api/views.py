from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from ..models import Post, Comment
from .serializers import CommentSerializer, PostSerializer,\
                         UserSerializer
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication
from rest_framework import permissions
from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import User
from .permissions import IsAuthorOrReadOnly

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    authentication_classes = (SessionAuthentication,)
    # custom class - IsAuthorOrReadOnly
    # the name is self-explanatory
    permission_classes = (permissions.IsAuthenticated,
                          IsAuthorOrReadOnly)

    def list(self, request):
        queryset = Post.objects.all()
        context = {'request': request}
        serializer = PostSerializer(queryset, many=True,
                                       context=context)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        queryset = Post.objects.all()
        context = {'request': request}
        post = get_object_or_404(queryset, pk=pk)

        serializer = PostSerializer(post, context=context)
        return Response(serializer.data)

    def create(self, request, pk=None):
        serializer = PostSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_post = serializer.create(serializer.validated_data)
        new_post.author = request.user
        new_post.save()
        return Response({'status': 'post created'})

    # action for adding a first-level comment to a post
    # we want all authenticated users to be able to add comments
    @action(detail=True, methods=['post', 'get'],
            permission_classes=[permissions.IsAuthenticated])
    def add_comment(self, request, pk=None):
        if request.method == 'POST':
            queryset = Post.objects.all()
            post = get_object_or_404(queryset, pk=pk)
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                new_comment = serializer.create()
                new_comment.author = request.user
                new_comment.parent = None
                # bind the comment to the post
                # on which the method has been called
                new_comment.post = post
                new_comment.save()
                return Response({'status': 'comment created'})
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.retrieve(request, pk=pk)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    authentication_classes = (SessionAuthentication,)
    permission_classes = (permissions.IsAuthenticated,
                          IsAuthorOrReadOnly)

    def get_queryset(self):
        # retrieve only next-level comments
        return Comment.objects.exclude(parent__isnull=False)

    def retrieve(self, request, pk=None):
        queryset = Comment.objects.all()
        context = {'request': request}
        comment = get_object_or_404(queryset, pk=pk)
        serializer = CommentSerializer(comment, context=context)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        queryset = Comment.objects.all()
        instance = get_object_or_404(queryset, pk=kwargs.get('pk'))
        # overwritten method
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        if instance.children.all():
            # If the comment has children,
            # we don't want to delete it entirely,
            # so that we can still see the replies.
            # Instead, we substitute its content with
            # "[deleted]", and remove user and time reference
            instance.text = '[deleted]'
            instance.author = None
            instance.created = None
            instance.save()
        else:
            parent = instance.parent
            super(CommentViewSet, self).perform_destroy(instance)
            # check whether its parent has no children left
            # if so, we call perform_destroy on its parent,
            # repeating the procedure for the latter
            if parent:
                # instance != None and author == None =>
                # => the comment has been deleted
                if not parent.author:
                    if parent.children.count() == 0:
                        self.perform_destroy(parent)

    def update(self, request, pk=None):
        queryset = Comment.objects.all()
        instance = get_object_or_404(queryset, pk=pk)
        context = {'request': request}
        serializer = CommentSerializer(instance,data=request.data,
                                       partial=True, context=context)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    # action for adding replies to comments
    # we want all authenticated users to be able to add comments
    @action(detail=True, methods=['post','get'],
            permission_classes=[permissions.IsAuthenticated])
    def add_comment(self, request, pk=None):
        if request.method == 'POST':
            queryset = Comment.objects.all()
            comment = get_object_or_404(queryset, pk=pk)
            serializer = CommentSerializer(data=request.data)
            if serializer.is_valid():
                new_comment = serializer.create()
                new_comment.author = request.user
                # bind the comment to the one on which
                # the method has been called
                new_comment.parent = comment
                new_comment.post = comment.post
                new_comment.save()
                return Response({'status': 'comment created'})
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return self.retrieve(request, pk=pk)

class CreateUserView(CreateAPIView):
    """
    Registration
    """
    model = User()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer