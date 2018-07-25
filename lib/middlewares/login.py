# coding:utf-8
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import HttpResponseRedirect
import re


exclued_path = [re.compile(item) for item in settings.EXCLUDE_URL]

# class LoginMiddleWare:
#     def process_request(self, request):
#         url_path = request.path
#         for item in exclued_path:
#             if re.match(item, url_path):
#                 return
#
#         if not request.user.is_authenticated:
#             return HttpResponseRedirect('/login/')


class LoginMiddleWare(MiddlewareMixin):
    def process_request(self, request):
        url_path = request.path
        for item in exclued_path:
            if re.match(item, url_path):
                return

        if not request.user.is_authenticated:
            return HttpResponseRedirect('/login/')

    # def process_response(self, request, response):
    #     return response
