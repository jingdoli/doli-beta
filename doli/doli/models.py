from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from swingtime.models import Event


class UserWidgets(models.Model):
    """docstring for UserWidgets
    """
    userid = models.ForeignKey(User, primary_key = True)
    #notesid = models.ForeignKey(notes)

 
