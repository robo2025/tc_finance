


from rest_framework.pagination import PageNumberPagination
from .response import APIResponse

class BasePaginationCustom(PageNumberPagination):
    page_size = 10
    max_page_size = 100
    page_size_query_param = 'limit'
    page_query_param = "offset"
    def get_paginated_response(self,data,request):
        page_size = int(self.get_page_size(request))
        page_number = int(request.query_params.get(self.page_query_param, 0))+1
        page_start=page_size*page_number-page_size
        page_end=page_size*page_number-1
        data = data[page_start:page_end+1]
        # return APIResponse(data=data,headers={
        #     'X-Content-Total':len(data),
        #     'X-Content-Range':"%d-%d"%(page_start,page_end)
        # })
        headers = {
             'X-Content-Total':len(data),
             'X-Content-Range':"%d-%d"%(page_start,page_end)
        }
        return data,headers













