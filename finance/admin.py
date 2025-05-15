from django.contrib import admin
from django.http import HttpResponse
from finance.models import Transaction, Goal
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats


class TransactionResource(resources.ModelResource):
    class Meta:
        model = Transaction
        fields = ('date', 'title', 'amount', 'transaction_type', 'category', 'user__email')  # Changed to email
        export_order = ('date', 'user__email', 'title', 'amount', 'transaction_type', 'category')  # Changed to email

    def dehydrate_user__email(self, transaction):  # Changed to email
        return transaction.user.email  # Changed to email


@admin.register(Transaction)
class TransactionAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = TransactionResource
    list_display = ['id', 'title', 'amount', 'transaction_type', 'date', 'category', 'user_email']  # Added user_email
    list_filter = ['transaction_type', 'category', 'date']
    search_fields = ['title', 'user__email']  # Changed to email
    date_hierarchy = 'date'
    
    def user_email(self, obj):  # New method to display user email
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    def get_export_queryset(self, request):
        """Override to filter by current user if not superuser"""
        qs = super().get_export_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs
    
    def get_export_formats(self):
        """Limit export formats to Excel and CSV"""
        return [base_formats.XLSX, base_formats.CSV]


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_email', 'name', 'target_amount', 'deadline']  # Changed to user_email
    list_filter = ['deadline']
    search_fields = ['name', 'user__email']  # Changed to email
    date_hierarchy = 'deadline'
    
    def user_email(self, obj):  # New method to display user email
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
    
    