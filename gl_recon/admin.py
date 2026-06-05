from django.contrib import admin

from .models import GLAccount, GLDailyBalance, GLPending, GLMapping
from .views import *
# Register your models here.
admin.site.register(GLAccount)
admin.site.register(GLDailyBalance)
admin.site.register(GLPending)
admin.site.register(GLMapping)