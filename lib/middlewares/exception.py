# coding:utf-8
import sys
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.views.debug import technical_500_response
from utils.http import APIResponseException
from utils.log import logger


class ExceptionMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        if settings.DEBUG:
            return None
        logger.error('request url:' + request.path + '\r' + str(exception))
        return APIResponseException(success=False, msg='服务器异常')


class UserBasedExceptionMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if request.user.is_superuser or request.META.get('REMOTE_ADDR') in settings.INTERNAL_IPS:
            return technical_500_response(request, *sys.exc_info())
