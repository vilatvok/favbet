from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, DemoWallet


admin.site.register(User, UserAdmin)


@admin.register(DemoWallet)
class DemoWalletAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'balance', 'is_active']
    list_filter = ['user']
    list_editable = ['balance', 'is_active']
