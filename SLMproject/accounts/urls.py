from django.urls import path
from .views import *

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path('users/<int:pk>/toggle-active/', ToggleUserActiveView.as_view(), name='toggle-user-active'),
    path('users/<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
]
