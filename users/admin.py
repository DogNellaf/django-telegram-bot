from django.contrib import admin

from users.models import User, Role, Event, Company


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'user_id', 'username',
        'created_at', 'updated_at', "company",
    ]
    list_filter = ["company", ]
    search_fields = ('username', 'user_id', 'company')


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'date', 'company']
    # search_fields = ('username', 'user_id')
