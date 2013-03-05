from django.contrib import admin
from .models import Instance

class InstanceAdmin(admin.ModelAdmin):
    list_display = ('name', 'ami', 'ip_address', 'start', 'end', 'state')

admin.site.register(Instance, InstanceAdmin)
