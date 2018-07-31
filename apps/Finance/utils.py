from decimal import Decimal,getcontextfrom FSys.config.extra import ORDER_API_HOSTfrom core.http.request import send_requestfrom utils.exceptions import PubErrorCustomfrom utils.cal import time_consumingfrom apps.Finance.order_model import (					Receipt)from apps.Finance.plan_model import (					PlanReceipt)from apps.Finance.models import (					FReceiptListDetail,					FReceiptList,					FReceipt,                    StatementDetail,                    CustomOrder,                    CustomPlanOrder)from apps.Finance.Custom.serializers import (                    FReceiptListDetailSerializer,                    FReceiptListSerializer,                    FReceiptSerializer)from apps.Finance.Custom.com_method import get_timedef set_receiptl_info(request,in_receipt=None,flag=2):    """    :memo 开票    :param request:    :param in_receipt:  开票结构    :param flag: 1-货款开票  2- 佣金开票    :return: {title,goods_merge,goods_list}    """    if not in_receipt:        raise PubErrorCustom("该订单不存在或已开票！")    title=None    goods_merge_object={}    receipt=FReceipt()    goods_merge_objects=[]    receipt_list_details=[]    for item in in_receipt:        if not title:            data=send_request(url="{}/api/receipt".format(ORDER_API_HOST),token=request.META.get('HTTP_AUTHORIZATION'),method='POST',data={})            if not data[0]:                raise PubErrorCustom("获取发票编号错误！")            receipt.receipt_sn = data[1]['open_receipt_sn']            receipt.guest_company_name = item.guest_company_name            receipt.tax_number = item.tax_number            receipt.receipt_type = item.receipt_type            receipt.receipt_title=item.title            receipt.receipt_addr=item.company_address            receipt.receipt_mobile=item.telephone            receipt.receipt_bank=item.bank            receipt.receipt_account=item.account            receipt.create_time=get_time()            receipt.flag=flag        else:            if title!=item.title:                raise PubErrorCustom("发票抬头不同,请重新选择！")        receipt_list_detail=FReceiptListDetail()        receipt_list_detail.receipt_sn=receipt.receipt_sn        receipt_list_detail.order_code=item.order_code        receipt_list_detail.goods_sn=item.goods_sn        receipt_list_detail.goods_name=item.goods_name        receipt_list_detail.model=item.model        receipt_list_detail.unit=item.unit        receipt_list_detail.number=item.number        receipt_list_detail.price=item.price        receipt_list_detail.goods_money=item.use_pay_total        receipt_list_detail.commission=item.use_commission        receipt_list_detail.receipt_money = item.ticket_amount        receipt_list_detail.order_time = item.order_time        receipt_list_detail.save()        receipt_list_details.append(receipt_list_detail)        receipt_list_detail.create_time=receipt.create_time        key=item.rest_type        if key not in goods_merge_object.keys():            goods_merge_object[key]=dict()            goods_merge_object[key]['receipt_sn']=receipt.receipt_sn            goods_merge_object[key]['name'] = key            goods_merge_object[key]['unit'] = receipt_list_detail.unit            goods_merge_object[key]['upd_time'] = receipt_list_detail.create_time            goods_merge_object[key]['number'] = receipt_list_detail.number            goods_merge_object[key]['price'] = receipt_list_detail.price            goods_merge_object[key]['rate'] = Decimal('0.16')            goods_merge_object[key]['money'] = receipt_list_detail.receipt_money            tax=goods_merge_object[key]['rate'] * abs(goods_merge_object[key]['money'])            if  goods_merge_object[key]['money']<0:                goods_merge_object[key]['taxfree_money'] = Decimal(0.0)- (abs(goods_merge_object[key]['money']) -  tax)                goods_merge_object[key]['tax_money']   = Decimal(0.0)-tax                goods_merge_object[key]['total_money'] = goods_merge_object[key]['taxfree_money'] + goods_merge_object[key]['tax_money']            else:                goods_merge_object[key]['taxfree_money'] = goods_merge_object[key]['money'] - tax                goods_merge_object[key]['tax_money'] =  tax                goods_merge_object[key]['total_money'] = goods_merge_object[key]['taxfree_money'] + goods_merge_object[key]['tax_money']        else:            money = receipt_list_detail.receipt_money            tax = abs(money) * goods_merge_object[key]['rate']            if  money<0:                tax   = Decimal(0.0)-tax                notax = Decimal(0.0)- (abs(money) -  tax)                ticket_money = notax + tax            else:                notax = money - tax                tax =  tax                ticket_money = notax + tax            goods_merge_object[key]['money'] += money            goods_merge_object[key]['taxfree_money'] += notax            goods_merge_object[key]['tax_money'] +=  tax            goods_merge_object[key]['total_money'] += ticket_money            goods_merge_object[key]['number'] += receipt_list_detail.number        title=item.title    goods_merge_list=[]    receipt.receipt_money = Decimal(receipt.receipt_money)    receipt.goods_money = Decimal(receipt.goods_money)    for  key,value in goods_merge_object.items():        value.pop('money')        # value['taxfree_money']=value['taxfree_money'].quantize(Decimal('0.00'))        # value['tax_money']=value['tax_money'].quantize(Decimal('0.00'))        # value['total_money']=value['total_money'].quantize(Decimal('0.00'))        goods_merge_list.append(value)        receipt_list=FReceiptList.objects.create(**value)        goods_merge_objects.append(receipt_list)        receipt.number += receipt_list.number        receipt.receipt_money += receipt_list.total_money        receipt.goods_money += receipt_list.total_money    receipt.save()    return {'title':receipt,'goods_merge':goods_merge_objects,'goods':receipt_list_details}@time_consumingdef noticket_query(where_sql="",params=[]):    """        未出票查询        :return:  statement    """    print(params)    print(where_sql)    statement = StatementDetail.objects.raw("""	    SELECT  t1.*,t1.id as statementdetail_ptr_id,t2.limit,	            t1.use_code as use_code,	            case	              when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_amount	              else t1.pay_total end as use_pay_total,	            case	              when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_commission	              else t1.commission end as use_commission,	            case	              when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_commission	              else t1.commission end as ticket_amount,	            '台'  as unit,	            t1.goods_name as rest_type	    FROM  statementdetail t1	    INNER JOIN  statement t2  ON  t1.code=t2.code and t2.status=3	    WHERE 1=1 {}	 """.format(where_sql),params)    statement=list(statement)    orders=[ item.use_code for item in statement ]    receipt = FReceiptListDetail.objects.raw("""            SELECT  t1.id,t1.order_code            FROM receiptlistdetail as t1            INNER JOIN receipt as t2 on t1.receipt_sn = t2.receipt_sn and t2.receipt_status=2 and flag=2            WHERE t1.order_code in %s        """, [orders])    obj=[]    for item in statement:        isFlag = True        for receipt_item in receipt:            if item.use_code == receipt_item.order_code:                if item.number - receipt_item.number <= 0:                    isFlag = False                    break                if item.use_code[:2]=='TH' :                    if abs(item.use_commission) - abs(receipt_item.total_money) > 0 :                        item.ticket_amount = Decimal( 0,0 ) - abs(item.use_commission) - abs(receipt_item.total_money)                else:                    if item.use_commission - receipt_item.total_money > 0:                        item.ticket_amount = item.use_commission - receipt_item.total_money                if item.number - receipt_item.number > 0:                    item.number = item.number - receipt_item.number        if isFlag:            obj.append(item)    return obj@time_consumingdef yesticket_query(where_sql="",params=[]):    """        已出票查询        :return:  statement    """    print(params)    print(where_sql)    statement = StatementDetail.objects.raw("""	    SELECT  t1.*,t1.id as statementdetail_ptr_id,t2.limit,t3.commission as commission1,	            t1.use_code as use_code,t4.receipt_no,t4.receipt_sn,	            case                when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_amount                else t1.pay_total end as use_pay_total,                case                when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_commission                else t1.commission end as use_commission,                case                when substr(t1.use_code,1,2)='TH' then 0.0 - t1.refund_commission                else t1.commission end as ticket_amount	    FROM  statementdetail t1	    INNER JOIN  statement t2  ON  t1.code=t2.code and t2.status=3	    INNER JOIN  receiptlistdetail t3 ON t1.use_code=t3.order_code	    INNER JOIN receipt t4 ON t3.receipt_sn  = t4.receipt_sn and receipt_status=2 and flag=2	    WHERE 1=1 {}	 """.format(where_sql),params)    return list(statement)@time_consumingdef yes_ticket_ready(where_sql="",params=[]):    """        已开票准备查询        :return:  statement    """    print(params)    print(where_sql)    statement = StatementDetail.objects.raw("""	    SELECT  t1.*,t1.id as statementdetail_ptr_id,t2.limit,t3.commission as commission1,	            t1.use_code as use_code	    FROM  statementdetail t1	    INNER JOIN  statement t2  ON  t1.code=t2.code and t2.status=3	    INNER JOIN  receiptlistdetail t3 ON t1.use_code=t3.order_code and	        t3.receipt_sn in (select receipt_sn from receipt where receipt_status=1 and flag=2)  {}	 """.format(where_sql),params)    return list(statement)def get_orders_obj(FA_flag=False,DD_flag=False,TH_flag=False,                        FA_where_sql=str(),FA_params=list(),DD_where_sql=str(),DD_params=list(),TH_where_sql=str(),TH_params=list(),                            DD_status=list(),TH_status=list(),FA_status=list()):    DD_params.insert(0,DD_status)    TH_params.insert(0,TH_status)    FA_params.insert(0,FA_status)    print(FA_where_sql,FA_params)    print(DD_where_sql,DD_params)    print(TH_where_sql,TH_params)    print("FA_status:" , FA_status)    print("DD_status:",  DD_status)    print("TH_status:",  TH_status)    if not FA_flag and not DD_flag and not TH_flag:        return [],[]    obj=[]    obj_FA=[]    if DD_flag:        obj1 = CustomOrder.objects.using('order').raw("""            SELECT                t1.id as orderdetail_ptr_id,                t1.*,t3.*,                t1.son_order_sn as order_code,                t1.goods_name as rest_type,                '台' as unit,                t1.add_time as order_time,                t1.univalent as price,                t1.subtotal_money as use_pay_total,                t1.commission as use_commission,                t1.subtotal_money as ticket_amount            FROM order_detail as t1            INNER JOIN  `order` as t2 on t1.`order`=t2.`id`            INNER JOIN  `receipt` as t3 on t2.`receipt` = t3.`id` and length(t3.`tax_number`)>0             WHERE  t1.son_order_sn in (select son_order_sn from `order_operation_record` where order_sn=t1.son_order_sn and status in {}) {}            """.format('%s',DD_where_sql),DD_params)        obj+=list(obj1)    if TH_flag:        obj  += list(CustomOrder.objects.using('order').raw("""                SELECT                    t1.id as orderdetail_ptr_id,                    t1.*,t3.*,                    t5.returns_sn as order_code,                    t1.goods_name as rest_type,                    '台' as unit,                    t1.add_time as order_time,                    t1.univalent as price,                    0.0 - t1.subtotal_money as use_pay_total,                    0.0 - t1.commission as use_commission,                    0.0 - t1.subtotal_money as ticket_amount                FROM order_detail as t1                INNER JOIN  `order` as t2 on t1.`order`=t2.`id`                INNER JOIN  `receipt` as t3 on t2.`receipt` = t3.`id` and length(t3.`tax_number`)>0                INNER JOIN  `order_returns` as t5 on t1.`son_order_sn` = t5.`order_sn`                WHERE   t1.son_order_sn in (select son_order_sn from `order_operation_record` where order_sn=t1.son_order_sn and status in {})  {}                """.format('%s',TH_where_sql),TH_params))    if FA_flag:        obj_FA += list(CustomPlanOrder.objects.using('plan_order').raw("""                SELECT                    t1.id as planorder_ptr_id,                    t1.*,t3.*,                    t1.plan_order_sn as order_code,                    '' as goods_sn,                    t1.plan_name as goods_name,                    t1.plan_name as model,                    case                       when t1.plan_name like '焊接' then '套'                      when t1.plan_name like '污水' then '台'                      else '台' end as unit,                    t1.add_time as order_time,                    t1.plan_name as rest_type,                    t1.total_money as price,                    t1.total_money as use_pay_total,                    0.0 as use_commission,                    t1.total_money as ticket_amount                FROM plan_order as t1                INNER JOIN  `receipt` as t3 on t1.`receipt_id` = t3.`id`                WHERE t1.status in {} and length(t3.`tax_number`)>0 {}                """.format('%s',FA_where_sql),FA_params))    return obj,obj_FAdef nogoodsticket_query(obj=[],obj_FA=[]):    orders=[item.order_code for item in obj_FA ]    orders1= [item.order_code for item in obj ]    obj_tmp = []    if len(orders):        receipt=FReceiptListDetail.objects.raw("""                SELECT  t1.id,t1.order_code,t3.`number`,t3.total_money                FROM receiptlistdetail as t1                INNER JOIN receipt as t2 on t1.receipt_sn = t2.receipt_sn and t2.receipt_status=2 and flag=1                INNER JOIN receiptlist as t3 on t1.receipt_sn=t3.receipt_sn                WHERE t1.order_code in %s            """,[orders])        for item in obj_FA:            isFlag=True            for receipt_item in receipt:                if item.order_code==receipt_item.order_code and item.order_code[:2]=='FA':                    #if item.use_pay_total - receipt_item.total_money <= 0 or item.number - receipt_item.number <=0 :                    if item.number - receipt_item.number <= 0:                        isFlag=False                        break                    if item.use_pay_total - receipt_item.total_money > 0:                        item.ticket_amount = item.use_pay_total - receipt_item.total_money                    if item.number - receipt_item.number > 0 :                        item.number= item.number - receipt_item.number            if isFlag:                obj_tmp.append(item)    if len(orders1):        receipt=FReceiptListDetail.objects.raw("""                SELECT  t1.id,t1.order_code                FROM receiptlistdetail as t1                INNER JOIN receipt as t2 on t1.receipt_sn = t2.receipt_sn and t2.receipt_status=2 and flag=1                WHERE t1.order_code in %s            """,[orders1])        for item in obj:            isFlag=True            for receipt_item in receipt:                if item.order_code==receipt_item.order_code :                    isFlag=False                    break            if isFlag:                obj_tmp.append(item)    obj_tmp.sort(key=lambda x: x.add_time, reverse=True)    return obj_tmp@time_consumingdef yesgoodsticket_query(where_sql="",params=[]):    """        已开票准备查询        :return:  statement    """    print(params)    print(where_sql)    obj = FReceiptListDetail.objects.raw("""        SELECT               t1.id as receiptlistdetail_ptr_id,              t1.*,              t2.receipt_no,              t2.receipt_type,              t2.create_time,              t2.guest_company_name,              case                 when substr(t1.order_code,1,2)='TH' then '退货单'                else '订单' end as order_type        FROM  receiptlistdetail as t1        INNER JOIN receipt as t2  on t1.receipt_sn=t2.receipt_sn and t2.receipt_status=2 and t2.flag=1        WHERE 1=1 {} order by t2.create_time desc    """.format(where_sql),params)    return list(obj)def get_FA_DD_TH(orders):    FA=[]    DD=[]    TH=[]    for item in orders:        if item[:2] == 'FA':            FA.append(item)        elif item[:2] == 'DD':            DD.append(item)        elif item[:2] == 'TH':            TH.append(item)        else:            raise PubErrorCustom("订单号有误！")    return FA,DD,THdef run_FA_DD_TH(orders=[]):    FA,DD,TH=get_FA_DD_TH(orders)    FA = [item for item in FA if item in orders]    DD = [item for item in DD if item in orders]    TH = [item for item in TH if item in orders]    if len(FA):        FA = PlanReceipt.objects.using('plan_order').raw("""            SELECT t1.id as receipt_ptr_id,t1.*,t2.plan_sn as order_code,t2.guest_company_name,t2.add_time as order_time            FROM receipt as t1            INNER JOIN plan_order as t2 ON t1.id=t2.receipt_id            WHERE t2.plan_sn in %s        """, [FA])    if len(DD):        DD = Receipt.objects.using('order').raw("""            SELECT t1.id as receipt_ptr_id,t1.*,t3.son_order_sn as order_code,t3.guest_company_name,t2.add_time as order_time            FROM receipt as t1            INNER JOIN `order` as t2 ON t1.id = t2.receipt            INNER JOIN `order_detail` as t3 ON t2.id = t3.`order`            WHERE t3.son_order_sn in %s        """, [DD])    if len(TH):        TH = Receipt.objects.using('order').raw("""            SELECT t1.id as receipt_ptr_id,t1.*,t4.returns_sn as order_code,t3.guest_company_name,t2.add_time as order_time            FROM receipt as t1            INNER JOIN `order` as t2 ON t1.id = t2.receipt            INNER JOIN `order_detail` as t3 ON t2.id = t3.`order`            INNER JOIN `order_returns` as t4 ON t3.son_order_sn=t4.order_sn            WHERE t4.returns_sn in %s        """, [TH])    return list(FA)+list(DD)+list(TH)def receipt_confirm_ex(request,flag=1):    receipt_sn = request.data.get('receipt_sn', "")    receipt_list = request.data.get('goods_merge', None)    if not receipt_sn:        raise PubErrorCustom("发票编号为空！")    finance_receipt = FReceipt.objects.filter(receipt_sn=receipt_sn)    if not finance_receipt.exists():        raise PubErrorCustom("该发票编号不存在！")    else:        finance_receipt = finance_receipt.first()        receipt_no = request.data.get('receipt_no', "")        custom = request.data.get('custom', "")        addr = request.data.get('addr', "")        mobile = request.data.get('mobile', "")        img = request.data.get('img', "")        finance_receipt.receipt_no = receipt_no        if custom:    finance_receipt.custom = custom        if addr:    finance_receipt.addr = addr        if mobile:    finance_receipt.mobile = mobile        if img:    finance_receipt.img = img        if flag==1:            finance_receipt=receipt_confirm(receipt_list, finance_receipt)        else:            finance_receipt = commission_receipt_confirm(receipt_list, finance_receipt)        finance_receipt.receipt_status = 2        finance_receipt.save()def receipt_confirm(receipt_list=None,receipt=None):    if not receipt: raise  PubErrorCustom("无此发票！")    if isinstance(receipt_list,list) and len(receipt_list):        item=receipt_list[0]        obj=FReceiptList.objects.filter(id=item['id'])        if not obj.exists():            raise PubErrorCustom("数据异常！")        obj=obj[0]        if 'goods_name' in item and item['goods_name']:            obj.name= item['goods_name']        if 'unit' in item and item['unit']:            obj.unit = item['unit']        if 'tax_rate' in item and item['tax_rate']:            obj.rate = item['tax_rate'] / Decimal ( 100.0)        if 'notax' in item and item['notax']:            obj.taxfree_money = item['notax']        if 'tax' in item and item['tax']:            obj.tax_money = item['tax']        if 'ticket_money' in item and item['ticket_money']:            obj.total_money = item['ticket_money']            receipt.receipt_money = item['ticket_money']        if 'number' in item and item['number']:            number_tmp = obj.number            receipt.number = item['number']            obj.number = item['number']            detailobj = FReceiptListDetail.objects.filter(receipt_sn=receipt.receipt_sn)            if not detailobj.exists():                raise PubErrorCustom("数据有误！")            if detailobj[0].order_code[:2] == 'FA':                order_obj,order_obj_FA=get_orders_obj(FA_flag=True, DD_flag=False, TH_flag=False,FA_where_sql=" and t1.plan_order_sn in %s", FA_params=[[detailobj[0].order_code]])                obj1 = nogoodsticket_query(order_obj,order_obj_FA)                if receipt.receipt_status==1:                    if not len(obj1):                        raise PubErrorCustom("开票数量超限！")                    elif obj1[0].number - item['number']  < 0:                        raise PubErrorCustom("开票数量超限！")                else:                    if not len(obj1):                        if number_tmp < item['number']  :                            raise PubErrorCustom("开票数量超限！")                    elif obj1[0].number - item['number'] < 0:                        raise PubErrorCustom("开票数量超限！")        obj.save()    return receiptdef commission_receipt_confirm(receipt_list=None,receipt=None):    if not receipt: raise  PubErrorCustom("无此发票！")    # if isinstance(receipt_list,list) :    #     for item in receipt_list:    #         obj=FReceiptList.objects.filter(id=item['id'])    #         if not obj.exists():    #             raise PubErrorCustom("数据异常！")    #         obj=obj[0]    #         if 'goods_name' in item and item['goods_name']:    #             obj.name= item['goods_name']    #         if 'unit' in item and item['unit']:    #             obj.unit = item['unit']    #         if 'tax_rate' in item and item['tax_rate']:    #             obj.rate = item['tax_rate'] / Decimal ( 100.0)    #         if 'notax' in item and item['notax']:    #             obj.taxfree_money = item['notax']    #         if 'tax' in item and item['tax']:    #             obj.tax_money = item['tax']    #         if 'ticket_money' in item and item['ticket_money']:    #             obj.total_money = item['ticket_money']    #             receipt.receipt_money = item['ticket_money']    #         if 'number' in item and item['number']:    #             number_tmp = obj.number    #             receipt.number = item['number']    #             obj.number = item['number']    #             detailobj = FReceiptListDetail.objects.filter(receipt_sn=receipt.receipt_sn)    #             if not detailobj.exists():    #                 raise PubErrorCustom("数据有误！")    #    #             get_FA_DD_TH()    #             order_obj,order_obj_FA=get_orders_obj(FA_flag=True,DD_flag=True,TH_flag=True,FA_where_sql=" and t1.plan_order_sn in %s", FA_params=[[detailobj[0].order_code]])    #             obj1 = nogoodsticket_query(order_obj,order_obj_FA)    #    #             if receipt.receipt_status==1:    #                 if not len(obj1):    #                     raise PubErrorCustom("开票数量超限！")    #                 elif obj1[0].number - item['number']  < 0:    #                     raise PubErrorCustom("开票数量超限！")    #             else:    #                 if not len(obj1):    #                     if number_tmp < item['number']  :    #                         raise PubErrorCustom("开票数量超限！")    #                 elif obj1[0].number - item['number'] < 0:    #                     raise PubErrorCustom("开票数量超限！")    #         obj.save()    return receipt