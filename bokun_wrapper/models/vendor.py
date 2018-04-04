from django.db import models
from jsonfield import JSONField


class Vendor(models.Model):
    bokun_id = models.CharField(unique=True, max_length=255)
    title = models.CharField(max_length=255)
    json = JSONField()
