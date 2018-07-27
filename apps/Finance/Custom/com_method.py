
import time
from datetime import datetime
import uuid
from dateutil.relativedelta import relativedelta
from openpyxl import Workbook
import calendar as cal
import requests,json

from  .response import APIResponse

from FSys.settings import SUPPLIER_API_HOST,ORDER_API_HOST,BASE_DIR

from .log import logger

from .error import BusiCustomError

from .export_data import export_rule

def timestamp_to_date(timestamp):
    """时间戳转日期格式"""
    time_arr = time.localtime(float(timestamp))
    date = time.strftime('%Y-%m-%d', time_arr)
    return date




def timestamp_to_datetime(timestamp):
    """时间戳转日期时间格式"""
    time_arr = time.localtime(float(timestamp))
    date = time.strftime('%Y-%m-%d %H:%M:%S', time_arr)
    return date


def datetime_to_timestamp(dt):
    """日期时间格式转时间戳"""
    dt=str(dt)
    if len(dt)==10:
        date = dt
        time_arr = time.strptime(date, '%Y-%m-%d')
    else:
        date=str(dt)[0:19]
        time_arr = time.strptime(date, '%Y-%m-%d %H:%M:%S')
    return time.mktime(time_arr)


#把datetime转成字符串
def datetime_toString(dt):
    return dt.strftime("%Y-%m-%d-")

#把字符串转成datetime
def string_toDatetime(string):
    return datetime.strptime(string, "%Y-%m-%d")

#把字符串转成时间戳形式
def string_toTimestamp(strTime):
    return time.mktime(string_toDatetime(strTime).timetuple())

#把时间戳转成字符串形式
def timestamp_toString(stamp):
    return time.strftime("%Y-%m-%d", time.localtime(stamp))

#把datetime类型转外时间戳形式
def datetime_toTimestamp(dateTim):
    return time.mktime(dateTim.timetuple())

def get_time():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def get_date():
    return time.strftime("%Y-%m-%d")

#月份相减
def month_sub(datet=get_time,m=0):
    return datet- relativedelta(months=m)

# 获取供应商信息
def Get_Supplier(supplier_id):
    res=requests.get(SUPPLIER_API_HOST + '/service/suppliers/%s' % supplier_id,verify=False)
    try:
        return json.loads(res.text)['data']
    except :
        return {}

# 获取自生成ID
def Get_Rule_Code(type=None):
    if type:
        """
            获取对账单号
            1: 对账单
            2: 收款单
            3: 付款单
            4: 结算单
        """
        headers = {'content-type': 'application/json',
               'users-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
        parameters = json.dumps({'finance_type': type})
        response = requests.post(ORDER_API_HOST + '/api/finance', data=parameters, headers=headers, verify=False)
        response_dict = json.loads(response.text)
        return response_dict['data']['ticket_id']



def get_open_receipt_sn():
    """获取开票sn"""
    """获取对账单号"""
    headers = {'content-type': 'application/json', \
               'users-agent': "User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"}
    parameters = json.dumps({})
    try:
        response = requests.post(ORDER_API_HOST + '/api/receipt', data=parameters, headers=headers, verify=False)
        response_dict = json.loads(response.text)
    except Exception as e:
        return None
    return response_dict


def list_to_query_format(param=list()):
    """
        列表转化为数据库查询条件格式
    """
    if not len(param):
        return "()"
    elif len(param)==1:
        return str(tuple(param)).replace(',','')
    else:
        return str(tuple(param))

# 获取当月第一天和最后一天
def Get_mse_day(year,month):
    return "%04d-%02d-01"%(year,month),"%04d-%02d-%02d"%(year,month,cal.monthrange(year,month)[1])

# 获取当月第一天和最后一天
def Get_mse_day_msg(year,month):
    return "%04d年%02d月01日"%(year,month),"%04d年%02d月%02d日"%(year,month,cal.monthrange(year,month)[1])


class table_export:
    def trade_condit(self):
        rulecode=str(self).split(' ')[0].split('.')[3]
        assert rulecode , "系统异常！"
        rule_object=None
        is_find=False
        for key in export_rule:
            if is_find:
                break
            elif key!=rulecode:
                continue
            else:
                for key1 in export_rule[key]:
                    if key1=="1==1":
                        rule_object = export_rule[key][key1]
                        is_find=True
                        break
                    else:
                        if len(key1.split('.'))>1:
                            try:
                                bool=eval(key1)
                            except NameError as e:
                                bool=False
                            if not bool:
                                continue
                        else:
                            k=key1.split('==')[0]
                            v=str(self.request.query_params.get(k, None))
                            exec("%s = %s"%(k,v))
                            try:
                                bool=eval(key1)
                            except NameError as e:
                                bool = False
                            if not bool:
                                continue
                        rule_object=export_rule[key][key1]
                        is_find=True
                        break
        return rule_object

    def item_check_key(key,value,key1):
        key1_arry=key1.split('.')

        for i, key1 in enumerate(key1_arry):
            if key1!=key:
                return False
            if i>0:
                if key1 not in value[key]:
                    return False
                else:
                    value=value[key]
                    key=key1
        return True

    def get_object_data(self,data,rule_object):
        table_value=[]
        for data_item in data:
            export_data = []
            for rule_item in rule_object:
                for key in data_item.keys():
                    try:
                        if not table_export.item_check_key(key,data_item,rule_item['field']):
                            continue
                        t = "data_item"
                        for i in rule_item['field'].split('.'):
                            t += "['%s']" % (i)
                        if 'func' in rule_item:
                            export_data.append(rule_item['func'](eval(t)))
                        else:
                            export_data.append(eval(t))
                            break
                    except KeyError as e:
                        continue
                    except NameError as e:
                        continue
            table_value.append(export_data)
        return table_value

    def export(self,data,request):
        export_flag=request.query_params.get("export", False)
        if str(export_flag)!='1':
            return data

        rule_object=table_export.trade_condit(self)
        if not rule_object:
            raise BusiCustomError("不能匹配导出规则！")

        title=[]
        table_value=[]
        if isinstance(rule_object,dict):
            for key in rule_object:
                title.append([item['field_name'] for item in rule_object[key]])
        else:
            title.append([ item['field_name'] for item in rule_object ])

        if isinstance(rule_object, dict):
            for key in rule_object:
                table_value.append( table_export.get_object_data(self,data,rule_object[key]))
        else:
            table_value.append(table_export.get_object_data(self, data, rule_object))

        execl_work = Workbook()
        execl = execl_work.active
        execl.title = "data"
        for i in range(len(title)):
            execl.append(title[i])
            [execl.append(item) for item in table_value][i]



        filename="/media/%s.xlsx"%(str(uuid.uuid1()))
        execl_work.save(filename = "%s%s"%(BASE_DIR,filename))
        return {'url':filename}

from decimal import Decimal
class float_math:

    def add(t1,t2):
        return Decimal(float(t1)+float(t2))

    def sub(t1,t2):
        return Decimal(float(t1)-float(t2))

    def mul(t1,t2):
        return Decimal(float(t1)*float(t2))


#
# class StatementDetailExport:
#     def export(data):
#
#



