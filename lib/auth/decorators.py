from django.views.decorators.csrf import csrf_exempt

from functools import wraps

from rest_framework import exceptions

from utils.http import APIResponse, http_response
from auth import get_user
from utils.response import ResCode


def token_required(view_func):
    """Decorator which ensures the users has provided a correct users and token pair."""

    @csrf_exempt
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        request.user, msg, status_code, rescode = get_user(request)
        if not request.user.is_authenticated:
            Response = http_response.get(status_code, APIResponse)
            return Response(rescode=rescode, msg=msg)
        return view_func(self, request, *args, **kwargs)

    return _wrapped_view


def operation_required(view_func):
    @csrf_exempt
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if request.user.user_type != 3:
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非管理员用户，无权限访问'
            raise exceptions.APIException(detail)
        return view_func(self, request, *args, **kwargs)

    return _wrapped_view
