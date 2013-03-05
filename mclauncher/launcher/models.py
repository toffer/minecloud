from django.contrib.auth.models import User
from django.db import models

class Instance(models.Model):
    launched_by = models.ForeignKey(User)
    name = models.CharField(max_length=20)
    ami =  models.CharField(max_length=20)
    ip_address = models.IPAddressField(null=True, blank=True)
    start= models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=30)

    def __unicode__(self):
        return "%s: %s" % (self.id, self.name)

class Session(models.Model):
    user = models.ForeignKey(User)
    instance = models.ForeignKey(Instance)
    login = models.DateTimeField()
    logout = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "instance", "login")

    def __unicode__(self):
        return "%s, %s" % (self.user, self.instance)
