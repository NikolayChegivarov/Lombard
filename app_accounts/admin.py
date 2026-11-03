from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_1c', 'consent_pd_given', 'consent_pd_date',
                    'created_at', 'last_sync_at')
    list_filter = ('consent_pd_given',)
    search_fields = ('user__username', 'id_1c')
    readonly_fields = ('user', 'id_1c', 'created_at', 'last_sync_at')

    def has_add_permission(self, request):
        # Профили создаются только автоматически при первом входе
        return False

    def has_delete_permission(self, request, obj=None):
        # Не даём удалять через админку — только через shell/скрипт при необходимости
        return False