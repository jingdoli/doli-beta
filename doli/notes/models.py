from django.db import models
from django.contrib.auth.models import User
class Notes(models.Model):
    """Model to save our note"""
    user = models.ForeignKey(User)
    title   = models.CharField(max_length=255)
    content = models.TextField()
    #automatically add timestamps when object is created 
    added_at = models.DateTimeField(auto_now_add=True) 
    #automatically add timestamps when object is updated
    last_update = models.DateTimeField(auto_now=True) #
# Create your models here.
