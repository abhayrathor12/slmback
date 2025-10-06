from django.urls import path
from .views import UserRegisterView, UserLoginView, UserListView, UserDetailView,LogoutView

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
]
