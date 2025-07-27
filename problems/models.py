from django.db import models
from registration.models import User

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
    ]
    
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    description = models.TextField()
    tags = models.CharField(max_length=500, blank=True)  # Comma-separated
    languages = models.CharField(max_length=200, blank=True)  # Comma-separated
    acceptance_rate = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    submissions = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    examples = models.TextField(blank=True)  # Store as JSON or formatted text
    constraints = models.TextField(blank=True)
    follow_up = models.TextField(blank=True)

    python_template = models.TextField(blank=True)
    javascript_template = models.TextField(blank=True)
    java_template = models.TextField(blank=True)
    cpp_template = models.TextField(blank=True) 
    c_template = models.TextField(blank=True)

    def __str__(self):
        return self.title
    
    def get_tags_list(self):
        """Returns tags as a list"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
    
    def get_languages_list(self):
        """Returns languages as a list"""
        return [lang.strip() for lang in self.languages.split(',') if lang.strip()]
    
    class Meta:
        ordering = ['-created_at']

class Submission(models.Model):
    id = models.AutoField(primary_key=True)
    STATUS_CHOICES = [
        ('Accepted', 'Accepted'),
        ('Wrong Answer', 'Wrong Answer'),
        ('Time Limit Exceeded', 'Time Limit Exceeded'),
        ('Runtime Error', 'Runtime Error'),
        ('Compilation Error', 'Compilation Error'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey('Problem', on_delete=models.CASCADE)
    code = models.TextField()
    language = models.CharField(max_length=20)
    verdict = models.CharField(max_length=20)
    score = models.FloatField(default=0)
    runtime = models.FloatField(default=0)
    memory_used = models.FloatField(default=0)
    test_cases_passed = models.IntegerField(default=0)
    total_test_cases = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    
    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
            return f"{self.user.firstname} {self.user.lastname} - {self.problem.title} - {self.status}"

class TestCase(models.Model):
    problem = models.ForeignKey('Problem', related_name='testcases', on_delete=models.CASCADE)
    input = models.TextField()
    expected_output = models.TextField()
    is_sample = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.problem.title} - Test Case {self.id}"


