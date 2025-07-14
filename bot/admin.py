from django.contrib import admin
from .models import ChannelsToSubscribe, User

@admin.register(ChannelsToSubscribe)
class ChannelsToSubscribeAdmin(admin.ModelAdmin):
    list_display = ('link', 'name')
    search_fields = ('link', 'name')
    list_filter = ('name',)
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('tg_id',)
    search_fields = ('tg_id',)
    list_filter = ('tg_id',)

