from django.contrib import admin
from rotten_potatoes.models import *

# Register your models here.
class MovieAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}


admin.site.register(Movie, MovieAdmin)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(UserProfile)
