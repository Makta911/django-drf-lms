from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Payment

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'city', 'avatar')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, CustomUserAdmin)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'payment_date', 'course', 'lesson')
    list_filter = ('payment_method', 'payment_date')
    search_fields = ('user__email', 'course__title', 'lesson__title')
    ordering = ('-payment_date',)