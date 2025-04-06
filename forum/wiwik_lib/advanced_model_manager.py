from typing import TypeVar, Sequence, Optional
from django.db import models

_T = TypeVar("_T", bound=models.Model, covariant=True)


class AdvancedModelManager(models.Manager):
    def __init__(
            self,
            select_related: Optional[Sequence[str]] = None,
            prefetch_related: Optional[Sequence[str]] = None,
            deferred_fields: Optional[Sequence[str]] = None,
    ):
        super(AdvancedModelManager, self).__init__()
        self._select_related = select_related
        self._prefetch_related = prefetch_related
        self._deferred_fields = deferred_fields

    def get_queryset(self) -> models.QuerySet[_T]:
        qs = super(AdvancedModelManager, self).get_queryset()

        if self._select_related:
            qs = qs.select_related(*self._select_related)
        if self._prefetch_related:
            qs = qs.prefetch_related(*self._prefetch_related)
        if self._deferred_fields:
            qs = qs.defer(*self._deferred_fields)

        return qs
