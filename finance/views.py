from django.shortcuts import render, redirect, HttpResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from finance.forms import TransactionForm, GoalForm
from finance.models import Transaction, Goal
from django.db.models import Sum
from finance.admin import TransactionResource
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import Count  
from django.urls import reverse_lazy
from django.db.models.functions import ExtractMonth


# Create your views here.

from django.http import JsonResponse
    
class TransactionCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = TransactionForm()
        return render (request, 'finance/transaction_form.html',{'form':form})
    
    def post(self, request, *args, **kwargs):
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            messages.success(request, 'Transaction Added Successfully!')
            return redirect('dashboard')
            
        return render (request, 'finance/transaction_form.html',{'form':form})
    
class TransactionListView(LoginRequiredMixin, View):
    def get (self, request):
        transaction = Transaction.objects.filter(user = request.user)
        return render (request, 'finance/transaction_list.html', {'transaction':transaction})
    
class GoalCreateView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        form = GoalForm()
        return render (request, 'finance/goal_form.html',{'form':form})
    
    def post(self, request, *args, **kwargs):
        form = GoalForm(request.POST)
        if form.is_valid():
            goal = form.save(commit=False)
            goal.user = request.user
            goal.save()
            return redirect('dashboard')
            
        return render (request, 'finance/goal_form.html',{'goal':goal})
    

def export_transactions(request):
    """View function to export transactions for the current user"""
    if not request.user.is_authenticated:
        return HttpResponse('Unauthorized', status=401)
    
    user_transactions = Transaction.objects.filter(user=request.user)
    transaction_resource = TransactionResource()
    dataset = transaction_resource.export(user_transactions)
    
    # Get the format (default to XLSX if not specified)
    export_format = request.GET.get('format', 'xlsx')
    
    if export_format == 'csv':
        excel_data = dataset.csv
        content_type = 'text/csv'
        file_extension = 'csv'
    else:  # default to xlsx
        excel_data = dataset.xlsx
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        file_extension = 'xlsx'
    
    response = HttpResponse(excel_data, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="user_{request.user.id}_transactions.{file_extension}"'
    return response

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        # Date ranges for reports
        today = date.today()
        last_month = today - timedelta(days=30)
        
        # Transaction data
        transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:5]
        
        # Summary calculations
        income_data = Transaction.objects.filter(
            user=request.user, 
            transaction_type='Income'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        expense_data = Transaction.objects.filter(
            user=request.user, 
            transaction_type='Expense'
        ).aggregate(
            total=Sum('amount'),
            count=Count('id')
        )
        
        total_income = income_data['total'] or 0
        total_expense = expense_data['total'] or 0
        net_savings = total_income - total_expense
        
        # Goal progress
        goals = Goal.objects.filter(user=request.user).order_by('deadline')
        goal_progress = []
        
        for goal in goals:
            progress = (goal.current_amount / goal.target_amount) * 100 if goal.target_amount > 0 else 0
            goal_progress.append({
                'goal': goal,
                'progress': min(100, progress),
                'remaining': max(0, goal.target_amount - goal.current_amount)
            })
        
        # Category breakdown for charts
        expense_categories = Transaction.objects.filter(
            user=request.user,
            transaction_type='Expense',
            date__gte=last_month
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        income_categories = Transaction.objects.filter(
            user=request.user,
            transaction_type='Income',
            date__gte=last_month
        ).values('category').annotate(
            total=Sum('amount')
        ).order_by('-total')
        
        # Fixed: Monthly trend data (SQLite compatible)
        monthly_trend = Transaction.objects.filter(
            user=request.user,
            date__year=today.year
        ).annotate(
            month=ExtractMonth('date')
        ).values('month', 'transaction_type').annotate(
            total=Sum('amount')
        ).order_by('month')
        
        context = {
            'transactions': transactions,
            'goals': goal_progress,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_savings': net_savings,
            'expense_categories': list(expense_categories),
            'income_categories': list(income_categories),
            'monthly_trend': list(monthly_trend),
            'current_year': today.year,
        }
        
        return render(request, 'finance/dashboard.html', context)

class ReportsView(LoginRequiredMixin, View):
    def get(self, request):
        # Get date range from request or default to last 30 days
        date_from = request.GET.get('from') or (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        date_to = request.GET.get('to') or date.today().strftime('%Y-%m-%d')
        
        # Convert to date objects
        try:
            date_from = date.fromisoformat(date_from)
            date_to = date.fromisoformat(date_to)
        except (ValueError, TypeError):
            messages.error(request, "Invalid date format")
            date_from = date.today() - timedelta(days=30)
            date_to = date.today()
        
        # Ensure date_from is before date_to
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        
        # Get transactions in date range
        transactions = Transaction.objects.filter(
            user=request.user,
            date__range=[date_from, date_to]
        )
        
        # Category breakdown
        expense_categories = transactions.filter(
            transaction_type='Expense'
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        income_categories = transactions.filter(
            transaction_type='Income'
        ).values('category').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        # Daily trend
        daily_trend = transactions.values('date', 'transaction_type').annotate(
            total=Sum('amount')
        ).order_by('date')
        
        context = {
            'date_from': date_from,
            'date_to': date_to,
            'expense_categories': list(expense_categories),
            'income_categories': list(income_categories),
            'daily_trend': list(daily_trend),
        }
        
        return render(request, 'finance/reports.html', context)

class ChartDataView(LoginRequiredMixin, View):
    def get(self, request):
        chart_type = request.GET.get('type', 'expense-categories')
        
        if chart_type == 'expense-categories':
            data = Transaction.objects.filter(
                user=request.user,
                transaction_type='Expense',
                date__month=date.today().month
            ).values('category').annotate(
                total=Sum('amount')
            ).order_by('-total')
            
            return JsonResponse({
                'labels': [item['category'] for item in data],
                'data': [float(item['total']) for item in data],
                'chart_type': 'pie'
            })
        
        elif chart_type == 'monthly-trend':
            monthly_data = Transaction.objects.filter(
                user=request.user,
                date__year=date.today().year
            ).extra(
                select={'month': "EXTRACT(month FROM date)"}
            ).values('month', 'transaction_type').annotate(
                total=Sum('amount')
            ).order_by('month')
            
            # Process into format suitable for line chart
            months = list(range(1, 13))
            income = [0] * 12
            expense = [0] * 12
            
            for item in monthly_data:
                month_idx = int(item['month']) - 1
                if item['transaction_type'] == 'Income':
                    income[month_idx] = float(item['total'])
                else:
                    expense[month_idx] = float(item['total'])
            
            return JsonResponse({
                'labels': [date(2000, m, 1).strftime('%b') for m in months],
                'datasets': [
                    {'label': 'Income', 'data': income, 'borderColor': '#4e73df'},
                    {'label': 'Expense', 'data': expense, 'borderColor': '#e74a3b'}
                ],
                'chart_type': 'line'
            })
        
        return JsonResponse({'error': 'Invalid chart type'}, status=400)