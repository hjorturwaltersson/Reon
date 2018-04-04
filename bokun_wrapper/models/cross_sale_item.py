from django.db import models
from jsonfield import JSONField

from .activity_property_mixin import ActivityPropertyMixin


class CrossSaleItem(ActivityPropertyMixin, models.Model):
    json = JSONField(null=True, blank=True)
