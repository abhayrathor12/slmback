from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'api/topics', TopicViewSet, basename="topic")
router.register(r'api/modules', ModuleViewSet, basename="module")
router.register(r'api/maincontents', MainContentViewSet, basename="maincontent")
router.register(r'api/pages', PageViewSet, basename="page")
router.register(r'api/admin/pages', AdminPageViewSet, basename='admin-pages')
router.register(r"api/quizzes", QuizViewSet, basename="quiz")

urlpatterns = [
    
    path("public/topics/", PublicTopicListView.as_view(), name="public_topics"),
    
    
    path("topics/", TopicListView.as_view(), name="topics"),
    path("modules/<int:pk>/", ModuleDetailView.as_view(), name="module-detail"),
    path("maincontents/<int:pk>/", MainContentDetailView.as_view(), name="maincontent-detail"),
    path("pages/<int:page_id>/", PageDetailView.as_view(), name="page-detail"),

    # Completion APIs
    path("pages/<int:page_id>/complete/", CompletePageView.as_view(), name="complete-page"),
    path("maincontents/<int:maincontent_id>/complete/", CompleteMainContentView.as_view(), name="complete-maincontent"),
    path("modules/<int:module_id>/complete/", CompleteModuleView.as_view(), name="complete-module"),

    # Quiz APIs
    path("quiz/<int:topic_id>/", QuizView.as_view(), name="quiz-detail"),
    path("quiz/<int:topic_id>/submit/", SubmitQuizView.as_view(), name="submit-quiz"),
    
    path("progress/summary/", UserProgressSummary.as_view(), name="user-progress-summary"),
path("api/dashboard-stats/", AdminDashboardStatsView.as_view()),
]+ router.urls