# coding:utf-8

class ResCode(tuple):
    Success = '10000'
    Error = '10001'
    # 验证
    Token_Missing = '20001'
    Token_Timed_Out = '20002'
    Token_Invalid = '20003'
    Login_Timed_Out = '20004'
    # 授权
    Access_Denied = '30001'

res_code = {
    'success': '10000',
    'error': '10001'
}

res = {
    'msg': '',
    'data': '',
    'rescode': res_code['success'],
}
