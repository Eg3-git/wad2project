from django.contrib import admin
from rotten_potatoes.models import *

# Register your models here.
admin.site.register(Movie)
admin.site.register(Genre)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(UserProfile)
