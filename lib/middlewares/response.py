import os
from django.http import FileResponse
from django.utils.deprecation import MiddlewareMixin

from utils.log import logger


class DeleteFileMiddleWare(MiddlewareMixin):
    def process_response(self, request, response):
        try:
            if isinstance(response, FileResponse):
                filename = getattr(response, 'filename')
                filepath = os.path.join(os.path.abspath('media'), filename)
                # if os.path.exists(filepath):
                #     os.remove(filepath)
        except Exception as ex:
            logger.error('delete error:{}'.format(ex))
        return response
