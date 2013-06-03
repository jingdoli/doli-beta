from django.utils.translation import ugettext_lazy as _
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from swingtime.models import Event

from tastypie.utils.timezone import now
from django.contrib.auth.models import User
from django.template.defaultfilters import slugify
from tastypie.models import create_api_key

models.signals.post_save.connect(create_api_key, sender=User)

class UserWidgets(models.Model):
    """docstring for UserWidgets
    """
    userid = models.ForeignKey(User, primary_key = True)
    #notesid = models.ForeignKey(notes)


class Entry(models.Model):
    user = models.ForeignKey(User)
    pub_date = models.DateTimeField(default=now)
    title = models.CharField(max_length=200)
    slug = models.SlugField()
    body = models.TextField()

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        # For automatic slug generation.
        if not self.slug:
            self.slug = slugify(self.title)[:50]

        return super(Entry, self).save(*args, **kwargs)
