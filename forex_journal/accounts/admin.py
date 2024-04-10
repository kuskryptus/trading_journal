from django.contrib import admin
from .models import CustomUser
# Register y
# our models h
# ere.


class CustomUserAdmin(admin.ModelAdmin):
    pass


admin.site.register(CustomUser, CustomUserAdmin)
