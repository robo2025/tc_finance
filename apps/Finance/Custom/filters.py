

class BaseCustomFilter:
    def filter(viewset,data_list):
        result_data=[]

        if not viewset.filters_custom:
            return data_list

        for data in list(data_list):
            condition = []
            for filter in viewset.filters_custom:
                if 'inkey' not in filter:
                    filter['inkey']=filter['key']
                if 'condition' not in filter:
                    filter['condition'] = 'eq'
                if 'all_query' not in filter:
                    filter['all_query'] = False

                try:
                    request_value=viewset.request.query_params.__getitem__(filter['inkey'])
                    if 'append' in filter:
                        request_value=str(request_value)+filter['append']
                    if  'func' in filter:
                        request_value=str(filter['func'](request_value))
                except KeyError:
                    condition.append(True)
                    continue
                if filter['all_query'] and (str(request_value)=='0' or str(request_value)=='all'):
                    condition.append(True)
                else:
                    if filter['condition'] == 'like':
                        condition.append(str(data[filter['key']]).find(request_value) != -1)
                    elif filter['condition'] == 'eq':
                        condition.append(str(data[filter['key']])==request_value)
                    elif filter['condition'] == 'gt':
                        condition.append(str(data[filter['key']]) > request_value)
                    elif filter['condition'] == 'gte':
                        condition.append(str(data[filter['key']]) >= request_value)
                    elif filter['condition'] == 'lt':
                        condition.append(str(data[filter['key']]) < request_value)
                    elif filter['condition'] == 'lte':
                        condition.append(str(data[filter['key']]) <= request_value)
                    else:
                        condition.append(True)

            if False not in condition:
                result_data.append(data)
        return result_data
