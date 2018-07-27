"""
Provides various authentication policies.
"""
from __future__ import unicode_literals

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication

from auth import get_user
from core_account.http.response import ResCode

class UserType:
    user = 1
    supplier = 2
    admin = 3
    super_admin = 4


class Authentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        return (request.user, None)


class UserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if request.user.user_type != 1:
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非普通用户，无权限访问'
            raise exceptions.APIException(detail)
        return (request.user, None)


class SupplierAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if request.user.user_type != 2:
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非供应商用户，无权限访问'
            raise exceptions.APIException(detail)
        return (request.user, None)


class AdminUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
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
        return (request.user, None)


class SupperAdminUserAuthentication(BaseAuthentication):
    def authenticate(self, request):
        request.user, msg, status_code, rescode = get_user(request)
        detail = {
            'rescode': rescode,
            'msg': msg,
            'status_code': status_code
        }
        if not request.user.is_authenticated:
            raise exceptions.APIException(detail)
        if request.user.user_type != 4:
            detail['status_code'] = 403
            detail['rescode'] = ResCode.Access_Denied
            detail['msg'] = '非超级管理员用户，无权限访问'
            raise exceptions.APIException(detail)
        return (request.user, None)


def check_authentication(request, expect_user_types):
    if request.user.user_type not in expect_user_types:
        detail = {
            'status_code': 403,
            'rescode': ResCode.Access_Denied,
            'msg': '非授权用户，无权限访问'
        }
        raise exceptions.NotAuthenticated(detail)
