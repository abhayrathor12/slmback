from django.db import models
from accounts.models import CustomUser

class Topic(models.Model):
    name = models.CharField(max_length=100)   # Python, VS Code, SQL
    order = models.IntegerField(default=0) 
    prize = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)# To maintain order

    def __str__(self):
        return self.name


class Module(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('hard', 'Hard'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')  # Added difficulty level
    

    def __str__(self):
        return f"{self.topic.name} - {self.title}"


class MainContent(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="main_contents")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class Page(models.Model):
    main_content = models.ForeignKey(MainContent, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=200, blank=True, default="Untitled Page")
    content = models.TextField()
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.main_content.title} - Page {self.order}"


class Progress(models.Model):
    """ Tracks module-level completion """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'module')


class MainContentProgress(models.Model):
    """ Tracks maincontent-level completion """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    main_content = models.ForeignKey(MainContent, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'main_content')


class PageProgress(models.Model):
    """ Tracks page-level completion (for sequential flow) """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    page = models.ForeignKey(Page, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'page')


class Quiz(models.Model):
    main_content = models.OneToOneField(MainContent, on_delete=models.CASCADE, related_name="quiz", null=True,
    blank=True)
    title = models.CharField(max_length=200)

    def __str__(self):
        return f"Quiz for {self.main_content.title}"



class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()

    def __str__(self):
        return self.text


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.text} ({'Correct' if self.is_correct else 'Wrong'})"


class QuizResult(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()
    passed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(auto_now_add=True)
