from django.contrib import admin
from .models import Payment

# Register your models here.


class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'payment_method',
        'payment_status',
        'transaction_id',
        'transaction_type',
        'paid_amount',
        'convenience_fee',
        'total_amount',
        'check_number',
        'excel_file',
        'pdf_file',
        'date'
    )
    list_filter = ('payment_method', 'payment_status', 'transaction_type', 'date')
    search_fields = ('order__id', 'transaction_id', 'check_number')
    readonly_fields = ('date',)

    fieldsets = (
        (None, {
            'fields': ('order', 'payment_method', 'payment_status', 'transaction_id', 'transaction_type')
        }),
        ('Amounts', {
            'fields': ('paid_amount', 'convenience_fee', 'total_amount')
        }),
        ('Check Payment Details', {
            'fields': ('check_number',)
        }),
        ('Files', {
            'fields': ('excel_file', 'pdf_file')
        }),
        ('Date & Time', {
            'fields': ('date',)
        }),
    )


admin.site.register(Payment, PaymentAdmin)
