from rest_framework import serializers
from ..models import *

class RecursiveField(serializers.Serializer):
    """
    Serializer for displaying nested comments
    """
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(
            value, context=self.context
        )
        return serializer.data

class FilterListSerializer(serializers.ListSerializer):
    """
    Serializer for filtering comments in post representation
    (leaving just first-level comments)
    """
    def to_representation(self, data):
        data = data.filter(parent=None)
        return super(FilterListSerializer, self).to_representation(data)

class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    children = RecursiveField(many=True, allow_null=True, read_only=True)
    class Meta:
        model = Comment
        fields = ('url','post','parent','text','created',
                  'updated', 'author', 'children')
        read_only_fields = ('author', 'created','updated',
                            'parent','post')
        # make only first-level comments show up in post view
        list_serializer_class = FilterListSerializer

    def create(self):
        # can only be called if the data
        # has been validated
        return Comment(**self.validated_data)

    def update(self, instance, validated_data):
        instance = super(CommentSerializer,self).update(instance, validated_data)
        return instance

class PostSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    comments = CommentSerializer(many=True, read_only=True)
    class Meta:
        model = Post
        fields = ('url', 'title', 'text', 'created','author',
                  'updated', 'comments')
        read_only_fields = ('author','created', 'updated')
        extra_kwargs = {'author': {'allow_null': True}}

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'},
                                     write_only=True)
    password2 = serializers.CharField(style={'input_type': 'password'},
                                     write_only=True)
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2',
                  'email', 'first_name', 'last_name')
        read_only_fields = ('id',)
        extra_kwargs = {'username': {'required': True},
                        'password': {'required': True},
                        'password2': {'required': True},
                        'email': {'required': True}}

    def is_valid(self, raise_exception=False):
        """
        We are overriding is_valid method in order to
        confirm that input passwords match
        """
        password = self.initial_data['password']
        password2 = self.initial_data['password2']
        if password != password2:
            raise serializers.ValidationError({
                'password': 'Passwords did not match.'
            })
        if len(password) < 8:
            raise serializers.ValidationError({
                'password': 'The password is too short'
            })
        if password.isdecimal():
            raise serializers.ValidationError({
                'password': 'The password is entirely numeric'
            })
        if not self.initial_data['email']:
            raise serializers.ValidationError({
                'email': 'Please enter the email'
            })

        return super(UserSerializer,self).is_valid(
            raise_exception=raise_exception
        )


    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )

        user.set_password(validated_data['password'])
        user.save()
        return user