from operator import attrgetter

from django.db import models, transaction
from django.db.models import prefetch_related_objects
import arrow

import logging


logger = logging.getLogger(__name__)


class ApiSyncModel(models.Model):
    initial_sync = models.DateTimeField(null=True, editable=False, db_index=True)
    last_sync = models.DateTimeField(null=True, editable=False, db_index=True)

    id = models.IntegerField(db_index=True)

    @classmethod
    def _sync_get_queryset(cls):
        return cls.objects.all()

    @classmethod
    def _sync(cls, normalized_api_response, prefetch_related=None, **kwargs):
        now = arrow.utcnow().datetime

        item_dict = {item['id']: item for item in normalized_api_response}
        item_id_set = set(item_dict.keys())

        obj_list = []

        # Update existing:
        existing_obj_qs = cls._sync_get_queryset().filter(id__in=list(item_id_set)).distinct()
        for obj in existing_obj_qs:
            update_fields = []
            for attr, value in item_dict[obj.id].items():
                if getattr(obj, attr) != value:
                    update_fields.append(attr)
                setattr(obj, attr, value)

            # Only save to database if something has changed:
            if update_fields:
                obj.last_sync = now
                obj.save(update_fields=update_fields)

            obj_list.append(obj)

        # Create missing:
        missing_item_id_set = item_id_set.difference([obj.id for obj in existing_obj_qs])

        created_obj_list = cls.objects.bulk_create([cls(
            initial_sync=now,
            last_sync=now,
            **item_dict[id]
        ) for id in missing_item_id_set])

        obj_list.extend(created_obj_list)

        if prefetch_related:
            prefetch_related_objects(obj_list, *prefetch_related)

        synced_data = sorted(obj_list, key=attrgetter('id'))

        cls.post_sync(
            synced_data=synced_data,
            normalized_api_response=normalized_api_response,
            **kwargs
        )

        return synced_data

    @classmethod
    @transaction.atomic
    def _sync_transaction(cls, *args, **kwargs):
        return cls._sync(*args, **kwargs)

    @classmethod
    def sync(cls, prefetch_related=None, **kwargs):
        raw_api_response = cls.fetch_data_from_api(**kwargs)

        normalized_api_response = cls.normalize_api_response(
            raw_api_response=raw_api_response,
            input=kwargs,
        )

        return cls._sync_transaction(
            normalized_api_response=normalized_api_response,
            raw_api_response=raw_api_response,
            prefetch_related=prefetch_related,
            input=kwargs,
        )

    @classmethod
    def post_sync(*args, **kwargs):
        pass

    @classmethod
    def fetch_data_from_api(cls, *args, **kwargs):
        raise NotImplementedError(
            'Method "fetch_data_from_api" of %s is not implemented' % cls.__name__)

    @staticmethod
    def normalize_api_response_item(**item):
        return item

    @classmethod
    def normalize_api_response(cls, raw_api_response, **kwargs):
        return (cls.normalize_api_response_item(**item) for item in raw_api_response)

    class Meta:
        abstract = True
        ordering = ['id']
