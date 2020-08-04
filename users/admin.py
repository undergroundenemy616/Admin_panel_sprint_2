from django.contrib import admin
from users.models import User, Account


class UserAdmin(admin.ModelAdmin):
    pass


class AccountAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Account, AccountAdmin)
