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
        path("conversation/", get_or_create_conversation, name="conversation"),
    path("send-message/", send_message, name="send_message"),
    path("submit-feedback/", submit_feedback, name="submit_feedback"),
    path("certificate/", StudentCertificateView.as_view()),
    path("admin/conversations/", AdminConversationListView.as_view()),
path("admin/conversation/<int:id>/", AdminConversationDetailView.as_view()),
path("admin/conversation/<int:convo_id>/send/", AdminSendMessageView.as_view()),
]
