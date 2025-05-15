from django.urls import path
from finance.views import DashboardView, TransactionCreateView,TransactionListView, GoalCreateView, export_transactions, ChartDataView, ReportsView

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('transaction/add/', TransactionCreateView.as_view(), name='transaction-add'),
    path('transaction/list', TransactionListView.as_view(), name='transaction-list'),
    path('transaction/goal/', GoalCreateView.as_view(), name='goal'),
    path('transaction/export/', export_transactions, name='export-transactions'),
    path('finance/chart-data/', ChartDataView.as_view(), name='chart-data'),
    path('reports/', ReportsView.as_view(), name='reports'), 
]
