from django.urls import path
from .views import *
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'api/topics', TopicViewSet, basename="topic")
router.register(r'api/modules', ModuleViewSet, basename="module")
router.register(r'api/maincontents', MainContentViewSet, basename="maincontent")
router.register(r'api/pages', PageViewSet, basename="page")
router.register(r"api/quizzes", QuizViewSet, basename="quiz")

urlpatterns = [
    
    path("admin_home",admin_home,name="admin_home"),
    path("",login_page,name="login_page"),
    path("register_page",register_page,name="register_page"),
    
    
    path("add_maincontent",add_maincontent,name="add_maincontent"),
    path("edit_maincontent/<int:pk>/", edit_maincontent, name="edit_maincontent"),
    
    path("public/topics/", PublicTopicListView.as_view(), name="public_topics"),
    
    path("add_page",add_page,name="add_page"),
    path("edit_page/<int:pk>/", edit_page, name="edit_page"),
    path("user_home",user_home,name="user_home"),
    
    path("add_quiz",add_quiz,name="add_quiz"),
    path("edit_quiz/<int:question_id>/", edit_quiz, name="edit_quiz"),
    
    path("add_topic",add_topic,name="add_topic"),
    path("edit_topic/<int:pk>/", edit_topic, name="edit_topic"),
    
    path("add_module",add_module,name="add_module"),
    path("module_page/<int:module_id>/", module_page, name="module_page"),
    path("edit_module/<int:pk>/", edit_module, name="edit_module"),
    
    path("pages_page/<int:page_id>/",pages_page,name="pages_page"),
    path("quiz_page",quiz_page,name="quiz_page"),
    
    
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

]+ router.urls