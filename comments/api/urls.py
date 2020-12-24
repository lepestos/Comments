from rest_framework.routers import DefaultRouter
from . import views
from django.urls import path, include

router = DefaultRouter()
router.register(r'posts', views.PostViewSet, basename='post')
router.register(r'comments', views.CommentViewSet,
                basename='comment')

#urlpatterns = router.urls

urlpatterns = [
    path('',include(router.urls)),
    path('register/', views.CreateUserView.as_view(),name="register")
]