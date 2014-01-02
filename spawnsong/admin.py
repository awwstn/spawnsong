from django.contrib import admin
from models import *
from sorl.thumbnail.admin import AdminImageMixin

#class SnippetAdmin(AdminImageMixin,admin.ModelAdmin):
class SnippetAdmin(admin.ModelAdmin):
    pass

admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Snippet, SnippetAdmin)
admin.site.register(Order)
admin.site.register(ArtistPayment)
admin.site.register(Comment)
