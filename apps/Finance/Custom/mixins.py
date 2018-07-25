

from django.http import Http404
from rest_framework import (viewsets,mixins)

from core.decorator.response import Core_connector

from ..Custom.pagination import BasePaginationCustom
from ..Custom.filters import BaseCustomFilter

class ListModelMixinCustom(mixins.ListModelMixin):
    @Core_connector(pagination=True)
    def list(self, request, *args, **kwargs):
        return self.get_serializer(self.get_queryset(),many=True).data

class CreateModelMixinCustom(mixins.CreateModelMixin):
    @Core_connector(transaction=True)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return []

class RetrieveModelMixinCustom(mixins.RetrieveModelMixin):
    @Core_connector()
    def retrieve(self, request, *args, **kwargs):
        return self.get_serializer(self.get_object()).data

class UpdateModelMixinCustom(mixins.UpdateModelMixin):
    @Core_connector(transaction=True)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        try:
            instance = self.get_object()
        except Http404:
            raise AssertionError("查无数据！")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}
        return []

class DestroyModelMixinCustom(mixins.DestroyModelMixin):
    @Core_connector(transaction=True)
    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except Http404:
            raise AssertionError("查无数据！")
        self.perform_destroy(instance)
        return []

class GenericViewSetCustom(viewsets.GenericViewSet):
    """
    Custom filtering
    """
    filter_custom_class = BaseCustomFilter
    filters_custom=None
    pagination_class = BasePaginationCustom

    def get_paginated_response(self, data,request):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data,request)

class ModelViewSetCustom(CreateModelMixinCustom,
                   RetrieveModelMixinCustom,
                   UpdateModelMixinCustom,
                   DestroyModelMixinCustom,
                   ListModelMixinCustom,
                    GenericViewSetCustom):
    """
    A viewset that provides default `create()`, `retrieve()`, `update()`,
    `partial_update()`, `destroy()` and `list()` actions.
    """
    pass

