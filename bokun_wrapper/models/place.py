from django.db import models
from jsonfield import JSONField


PLACE_TYPE_CHOICES = (
    ("hotel", "Hotel"),
    ("terminal", "Terminal"),
    ("airport", "Airport"),
    ("other", "Other")
)


class Place(models.Model):
    vendor_id = models.IntegerField()
    title = models.CharField(max_length=255)
    location = JSONField()
    json = JSONField()
    type = models.CharField(choices=PLACE_TYPE_CHOICES, max_length=200, default="hotel")
    ordering = models.IntegerField(default=0)


    def __str__(self):
        return self.title

    class Meta:
        ordering = ['ordering', 'title']
