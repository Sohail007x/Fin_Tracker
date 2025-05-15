from django.db import models
from accounts.models import CustomUser as User
from django.core.validators import MinValueValidator

class Transaction(models.Model):
    TRANSACTION_TYPE = [
        ('Income', 'Income'),
        ('Expense', 'Expense')
    ]
    
    CATEGORY_CHOICES = [
        ('Salary', 'Salary'),
        ('Investment', 'Investment'),
        ('Gift', 'Gift'),
        ('Food', 'Food'),
        ('Transport', 'Transport'),
        ('Entertainment', 'Entertainment'),
        ('Utilities', 'Utilities'),
        ('Shopping', 'Shopping'),
        ('Other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)
    date = models.DateField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount}"
    
    class Meta:
        ordering = ['-date']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'

class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    target_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    current_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )
    deadline = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} (${self.current_amount}/${self.target_amount})"
    
    class Meta:
        ordering = ['deadline']
        verbose_name = 'Goal'
        verbose_name_plural = 'Goals'