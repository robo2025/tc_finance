from utils.string_extension import safe_intclass Pagination:    def __init__(self):        self.page_size = 10        self.max_page_size = 100        self.page_size_query_param = 'limit'        self.page_query_param = "offset"    def _positive_int(self,integer_string, strict=False, cutoff=None):        """        Cast a string to a strictly positive integer.        """        ret = int(integer_string)        if ret < 0 or (ret == 0 and strict):            raise ValueError()        if cutoff:            return min(ret, cutoff)        return ret    def get_page_size(self,request):        try:            if self.page_size_query_param:                return self._positive_int(                    request.query_params[self.page_size_query_param],                    strict=True,                    cutoff=self.max_page_size                )        except (KeyError, ValueError):                pass        return self.page_size    def get_paginated(self,data, request):        page_size = int(self.get_page_size(request))        page_number = int(request.query_params.get(self.page_query_param, 0)) + 1        page_start = page_size * page_number - page_size        page_end = page_size * page_number - 1        data = data[page_start:page_end + 1]        headers = {            'X-Content-Total': len(data),            'X-Content-Range': "%d-%d" % (page_start, page_end)        }        return {'data':data,'header':headers}