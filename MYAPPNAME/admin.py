from django.contrib import admin
from models import *

class ActionTypeAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('enabled', 'label')
        }),
        ('Facebook', {
            'fields': ('facebook_post', 'message', 'link', 'photo',)
        }),
        # ('Advanced', {
        #     'classes': ('collapse',),
        #     'fields': ('hook_url',)
        # }),

    )

admin.site.register(ActionType, ActionTypeAdmin)

admin.site.register(AuthDataWhitelist)
