from django.db import models
from registration.models import User

class Problem(models.Model):
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20)
    tags = models.CharField(max_length=200)
    languages = models.CharField(max_length=200)  # Comma-separated list or ManyToMany

class Submission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    language = models.CharField(max_length=20, choices=[
        ('Python', 'Python'),
        ('C++', 'C++'),
        ('Java', 'Java'),
        ('JavaScript', 'JavaScript'),
    ])
    code = models.TextField()
    is_correct = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.problem.title}"


