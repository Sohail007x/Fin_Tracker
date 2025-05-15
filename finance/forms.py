from django import forms
from finance.models import Transaction, Goal
from django.core.exceptions import ValidationError
from datetime import date

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['title', 'amount', 'transaction_type', 'date', 'category', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'max': date.today().strftime('%Y-%m-%d'),
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        fields = ['name', 'target_amount', 'deadline']
        widgets = {
            'deadline': forms.DateInput(attrs={
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d'),
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
    
    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']
        if deadline < date.today():
            raise ValidationError("Deadline cannot be in the past")
        return deadline