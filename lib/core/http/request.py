

from requests import request
from utils.log import logger



def get_header(request, key, default=None):
    django_key = 'HTTP_%s' % key.upper().replace('-', '_')
    return request.META.get(django_key, default)

def get_client_ip(request):
    try:
        real_ip = request.META['HTTP_X_FORWARDED_FOR']
        real_ip = real_ip.split(',')[0]
    except:
        try:
            real_ip = request.META['REMOTE_ADDR']
        except:
            real_ip = ''
    return real_ip

def is_valid_ip(request):
    # ip = get_client_ip(request)
    # if ip in ['']:
    #     return True
    # return False

    return True

def get_token(request):
    return request.META.get('HTTP_AUTHORIZATION')

def send_request(url, token, method='get', params=None, data=None):
    try:
        result = request(method, url, headers={'Authorization': token}, params=params, data=data, verify=False)
        status_code = result.status_code
        result = result.json()
        if str(result.get('rescode')) == '10000':
            return True, result.get('data')
        return False, result.get('msg')
    except Exception as ex:
        logger.error('{0} 调用失败:{1}'.format(url, ex))
        return False, '{0}'.format(ex)