from django.db import models
from jsonfield import JSONField


class RequestLog(models.Model):
    url = models.URLField(null=True, blank=True)
    incoming_body = JSONField(null=True, blank=True)
    outgoing_body = JSONField(null=True, blank=True)
    bokun_response = JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
