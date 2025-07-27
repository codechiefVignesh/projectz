from django import forms
from .models import Problem

class ProblemForm(forms.ModelForm):
    class Meta:
        model = Problem
        fields = ['title', 'difficulty', 'description', 'tags', 'languages', 'acceptance_rate', 'submissions', 'testcases']
        
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. Two Sum, Binary Tree Traversal'
        })
    )
    
    difficulty = forms.ChoiceField(
        choices=[('', 'Select difficulty'), ('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'rows': 6,
            'placeholder': 'Describe the problem clearly. Include input/output examples if needed.'
        })
    )
    
    tags = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    languages = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )
    
    acceptance_rate = forms.DecimalField(
        required=False,
        max_digits=5,
        decimal_places=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. 49.2',
            'step': '0.1',
            'min': '0',
            'max': '100'
        })
    )
    
    submissions = forms.CharField(
        required=False,
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'e.g. 1.2M, 856K'
        })
    )
    
    testcases = forms.CharField(widget=forms.HiddenInput(), required=False)
