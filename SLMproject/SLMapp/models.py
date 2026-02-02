from django.db import models
from accounts.models import CustomUser

def format_duration(minutes):
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours} hr {mins} min"
    elif hours:
        return f"{hours} hr"
    else:
        return f"{mins} min"

class Topic(models.Model):
    name = models.CharField(max_length=100)   # Python, VS Code, SQL
    order = models.IntegerField(default=0) 
    prize = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)# To maintain order

    def __str__(self):
        return self.name


# models.py - THIS IS EXCELLENT! KEEP IT EXACTLY LIKE THIS
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
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')

    def __str__(self):
        return f"{self.topic.name} - {self.title}"

    @property
    def total_duration(self):
        return sum(main.total_duration for main in self.main_contents.all())

    @property
    def formatted_duration(self):
        return format_duration(self.total_duration)

    def save(self, *args, **kwargs):
        if not self.pk:  # Creating new
            if self.order <= 0:
                # Auto assign next order
                max_order = Module.objects.filter(topic=self.topic).aggregate(
                    models.Max('order')
                )['order__max']
                self.order = (max_order or 0) + 1
            else:
                # Insert at specific position → shift others down
                Module.objects.filter(
                    topic=self.topic,
                    order__gte=self.order
                ).update(order=models.F('order') + 1)
        else:  # Updating existing
            old = Module.objects.get(pk=self.pk)
            if old.order != self.order:
                if self.order < old.order:
                    # Moving up
                    Module.objects.filter(
                        topic=self.topic,
                        order__gte=self.order,
                        order__lt=old.order
                    ).exclude(pk=self.pk).update(order=models.F('order') + 1)
                elif self.order > old.order:
                    # Moving down
                    Module.objects.filter(
                        topic=self.topic,
                        order__lte=self.order,
                        order__gt=old.order
                    ).exclude(pk=self.pk).update(order=models.F('order') - 1)

        super().save(*args, **kwargs)


class MainContent(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="main_contents")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    @property
    def total_duration(self):
        """Sum of all page durations (in minutes)."""
        return sum(page.time_duration for page in self.pages.all())

    @property
    def formatted_duration(self):
        """Human-readable duration."""
        return format_duration(self.total_duration)


class Page(models.Model):
    main_content = models.ForeignKey(MainContent, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=200, blank=True, default="Untitled Page")
    content = models.TextField()
    order = models.IntegerField(default=0)
    time_duration = models.PositiveIntegerField(default=0, help_text="Duration in minutes")

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
