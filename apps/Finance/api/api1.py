
import os
import time
from decimal import Decimal
from rest_framework.decorators import detail_route, list_route

from apps.Finance.models import (PriceRule, RefundCheck, Statement, StatementDetail, CustomOrder,
                            FinanceReceipt, FinanceReceiptList, FinanceReceiptListDetail, CustomPayment, CustomPlanOrder)

from apps.Finance.order_model import OrderDetail,Receipt,Order,OrderRefund
from apps.Finance.pay_model import Payment,Refund

from apps.Finance.plan_model import PlanOrder

from apps.Finance.Custom.mixins import (ModelViewSetCustom, ListModelMixinCustom, GenericViewSetCustom)

from apps.Finance.Custom.serializers import (PriceRuleSerializer, RefundCheckSerializer,
                                        RefundOrderDetailsSerializer,
                                        CreateStatementSerializer,
                                        ModiStatementSerializer, StatementSerializer,
                                        StatementDetailSerializer, StatementDetailExSerializer,
                                        PayTranListSerializer, RefundPayTranListSerializer,
                                        OrderAllQuery, NoFinanceReceiptSerializer, FinanceReceiptSerializer, FinanceReceiptDetailSerializer,
                                        NoFinanceReceiptPlanOrderSerializer, NoFinanceReceiptPlanOrderDetailSerializer,
                                        NoFinanceReceiptSerializer1,FinanceReceiptDetailSerializer1)

from apps.Finance.Custom.response import APIResponse

from apps.Finance.utils import get_orders_obj


from apps.Finance.Custom.db import db

from utils.exceptions import PubErrorCustom
from core.http.request import send_request

from apps.Finance.Custom.com_method import float_math,Get_Rule_Code,datetime_to_timestamp,get_open_receipt_sn,get_time,list_to_query_format,get_date
#
from core.decorator.response import Core_connector
from FSys.config.extra import PAYMENT_API_HOST,PAYMENT_API_TOKEN

from auth.authentication import AdminUserAuthentication

#结算规则
class PriceruleViewSet(ModelViewSetCustom):
	filters_custom=[
	    {'key': "rulecode", 'condition': "like",},
	    {'key': "goods_name", 'condition': "like",},
	    {'key': "goods_model", 'condition': "like",},
	    {'key': "supplier_id",'all_query':True},
	    {'key': "start_date", 'condition': "gte",'inkey':'start_date' },
	    {'key': "start_date", 'condition': "lte", 'inkey': 'end_date'},
	]
	lookup_field = ('rulecode')
	
	def get_authenticators(self):
		if 'get' in self.action_map.keys():
			if self.action_map.get('get')!='getrate':
				return [auth() for auth in [AdminUserAuthentication]]
		else:
			return [auth() for auth in [AdminUserAuthentication]]
	
	def get_queryset(self):
	    return PriceRule.objects.filter().order_by('-add_time')
	def get_serializer_class(self):
	    return PriceRuleSerializer
	
	@Core_connector(transaction=True)
	def create(self, request, *args, **kwargs):
	    request_list=request.data.get('request_list', [])
	    if not len(request_list):
	        raise PubErrorCustom("请求列表空！")
	
	    for pricerule in request_list:
	        if not pricerule['supplier_id']:
	            raise PubErrorCustom("供应商ID为空！！")
	        if not pricerule['start_date']:
	            raise PubErrorCustom("生效日期为空！")
	        if not pricerule['end_date']:
	            raise PubErrorCustom("失效日期为空！")
	        if not pricerule['goods_sn']:
	            raise PubErrorCustom("商品号为空！")
	        if PriceRule.objects.filter(supplier_id=pricerule['supplier_id'],
	                                    goods_sn=pricerule['goods_sn']).exists():
	            raise PubErrorCustom("供应商[%s]商品[%s]规则已存在！"%(pricerule['supplier_name'],pricerule['goods_name']))
	        pricerule['rulecode']=Get_Rule_Code(type=4)
	        PriceRule.objects.create(**pricerule)
	    return []
	
	@Core_connector(transaction=True)
	def update(self, request, *args, **kwargs):
	    request_list=request.data.get('request_list', [])
	    if not len(request_list):
	        raise PubErrorCustom("请求列表空！")
	    for pricerule in request_list:
	        if not pricerule['rulecode']:
	            raise PubErrorCustom("结算规则编号为空！")
	        if not pricerule['start_date']:
	            raise PubErrorCustom("生效日期为空！")
	        if not pricerule['end_date']:
	            raise PubErrorCustom("失效日期为空！")
	        rule=PriceRule.objects.filter(rulecode=pricerule['rulecode'])
	        if not rule.exists():
	            raise PubErrorCustom("%s 查无数据"%(pricerule['rulecode']))
	        else:
	            rule=rule.first()
	            rule.rate=pricerule['rate']
	            rule.start_date=pricerule['start_date']
	            rule.end_date = pricerule['end_date']
	            rule.save()
	    return []
	
	@Core_connector(transaction=True)
	def destroy(self, request, *args, **kwargs):
	    rulecodes=request.data.get('rulecodes', [])
	    if not len(rulecodes):
	        raise PubErrorCustom("请选择要删除的记录！")
	    PriceRule.objects.filter(rulecode__in=rulecodes).delete()
	    return []

	@list_route(methods=['GET'])
	@Core_connector()
	def getrate(self, request, *args, **kwargs):
		"""
		获取供应商商品佣金比例
		"""
		goods_sn = dict(self.request.query_params).get('goods_sn',[])
		print(goods_sn)
		if not isinstance(goods_sn,list):
			raise PubErrorCustom("参数格式有误！")
		if not len(goods_sn):
			raise PubErrorCustom("商品ID为空！")
		date = get_date()

		data=[]
		obj = PriceRule.objects.filter(goods_sn__in=goods_sn, start_date__lte=date, end_date__gte=date)
		if obj.exists():
			for item in obj:
				data.append({'goods_sn':item.goods_sn,'rate':item.rate/100})

		data_r=[]
		for item in goods_sn:
			is_flag=True
			for obj in data:
				if item == obj['goods_sn']:
					is_flag=False
					break
			if is_flag:
				data_r.append({'goods_sn':item,'rate':0.0})
		return {'data':data+data_r}

#退款订单
class RefundOrderViewSet(ModelViewSetCustom):
    authentication_classes = [AdminUserAuthentication]
    filters_custom=[
        {'key': "order_date", 'condition': "gte", 'inkey':'start_dt' ,'func':datetime_to_timestamp,'append':" 00:00:00"},
        {'key': "order_date", 'condition': "lte", 'inkey': 'end_dt','func':datetime_to_timestamp,'append':' 23:59:59'},
        {'key': 'son_order_sn','condition': "like"},
        {'key':'cancel_status'}
    ]
    lookup_field = ("refund_sn")
    def get_queryset(self):
        return RefundCheck.objects.filter().order_by('-add_time')
    def get_serializer_class(self):
        return RefundCheckSerializer

    @Core_connector(pagination=True)
    def list(self, request, *args, **kwargs):
        cancel_status=self.request.query_params.get('cancel_status')
        if not cancel_status:
            raise PubErrorCustom("cancel_status不能为空！")

        if int(cancel_status)==1:
            sql = """      \
                     select              \
                         n.`order`                     as `order`,            \
                         n.son_order_sn                as son_order_sn,         \
                         n.supplier_name               as supplier_name ,       \
                         n.guest_company_name          as guest_company_name,   \
                         UNIX_TIMESTAMP(n.add_time)    as order_date ,          \
                         UNIX_TIMESTAMP(s.add_time)    as trade_cancel_date,    \
                         s.refund_type                 as trade_cancel_remark , \
                         case  s.refund_type       \
                           when s.refund_type=1    \
                             then (select responsible_party from order_cancel where order_sn=s.order_sn limit 1)     \
                           when s.refund_type in (2,3)   \
                             then (select responsible_party from abnormal_order where order_sn=s.order_sn limit 1) \
                           else 1     end             as trade_cancel_name ,   \
                         n.number * n.univalent        as trade_amount    ,     \
                         n.number * n.univalent        as trade_cancel_amount , \
                         s.refund_sn                   as refund_sn    ,       \
                         1                             as cancel_status        \
                     from order_refund s       \
                         inner join order_detail n               \
                     on s.order_sn=n.son_order_sn       \
                     and  s.status=1 order by s.add_time desc\
             """
            data = db('order').query_todict(sql)
            data_tmp=[]
            for item in data:
                if not RefundCheck.objects.filter(refund_sn=item['refund_sn']).exists():
                    data_tmp.append(item)
            # if 'pay_time' in data[0].keys():
            #     data.sort(key=lambda k: (k.get('pay_time', 0)), reverse=True)
            data=data_tmp
        else:
            data=self.get_serializer(self.get_queryset(), many=True).data
        return {"data":data}

    @Core_connector(transaction=True)
    def create(self,request,*args,**kwargs):

        refundcheck_obj=RefundCheck()
        refundcheck_obj.refund_sn=self.request.data['refund_sn']
        refundcheck_obj.trade_cancel_amount=float(self.request.data['trade_cancel_amount'])
        refundcheck_obj.pay_amount=float(self.request.data['pay_amount'])
        if refundcheck_obj.pay_amount > refundcheck_obj.trade_cancel_amount:
            raise PubErrorCustom("实退金额大于应退金额！")

        sql = """      \
                 select              \
                     n.`order`                     as `order`,            \
                     n.son_order_sn                as son_order_sn,         \
                     n.supplier_id                 as supplier_id ,       \
                     n.supplier_name               as supplier_name ,       \
                     p.guest_id                    as guest_id , \
                     n.guest_company_name          as guest_company_name,   \
                     n.add_time                    as order_date ,          \
                     s.add_time                    as trade_cancel_date,    \
                     s.refund_type                 as trade_cancel_remark , \
                     case  s.refund_type       \
                       when s.refund_type=1    \
                         then (select responsible_party from order_cancel where order_sn=s.order_sn limit 1)     \
                       when s.refund_type in (2,3)   \
                         then (select responsible_party from abnormal_order where order_sn=s.order_sn limit 1) \
                       else 1     end             as trade_cancel_name ,   \
                     n.number * n.univalent        as trade_amount    ,     \
                     n.number * n.univalent        as trade_cancel_amount , \
                     s.refund_sn                   as refund_sn    ,       \
                     2                             as cancel_status        \
                 from order_refund as s       \
                     inner join order_detail as   n     \
                     inner join `order` as  p \
                 on s.order_sn=n.son_order_sn   and   n.order=p.id  \
                 and  s.status=1 and s.refund_sn='%s'  order by s.add_time desc\
         """%(refundcheck_obj.refund_sn)
        print(sql)
        data = db('order').query_todict(sql)
        if not len(data) :
            raise PubErrorCustom("退款单号不存在！")
        elif len(data)!=1 :
            raise PubErrorCustom("数据有误！")
        data=data[0]

        refundcheck_obj.order_code = data['son_order_sn']
        refundcheck_obj.supplier_id = data['supplier_id']
        refundcheck_obj.supplier_name=data['supplier_name']
        refundcheck_obj.guest_id = data['guest_id']
        refundcheck_obj.guest_company_name = data['guest_company_name']
        refundcheck_obj.order_time = data['order_date']
        refundcheck_obj.trade_cancel_time = data['trade_cancel_date']
        refundcheck_obj.trade_cancel_remark = data['trade_cancel_remark']
        refundcheck_obj.responsible_party = data['trade_cancel_name']
        refundcheck_obj.trade_amount=data['trade_amount']
        refundcheck_obj.save()

        flag=send_request(url="%s/payment/refund"%(PAYMENT_API_HOST),token=request.META.get('HTTP_AUTHORIZATION'),method='POST',
                            data={
                                'order_no':refundcheck_obj.order_code,
                                'user_id':refundcheck_obj.guest_id,
                                'amount':refundcheck_obj.pay_amount,
                            })
        if not flag[0]:
            raise PubErrorCustom("退款失败！")
        return {"data":[]}

    @Core_connector()
    def retrieve(self, request, *args, **kwargs):
        return {"data":RefundOrderDetailsSerializer.data(kwargs.get('refund_sn', ''))}

#对账单
class StatementViewset(ModelViewSetCustom):
	authentication_classes = [AdminUserAuthentication]
	filters_custom=[
		{'key': "limit", 'condition': "gte", 'inkey': 'start_ym','func':lambda x:x.replace('-','')},
		{'key': "limit", 'condition': "lte", 'inkey': 'end_ym','func':lambda x:x.replace('-','')},
		{'key': "status" ,},
		{'key': "supplier_id",'all_query':True},
	]
	lookup_field = ("code")
	def get_queryset(self):
		if self.action=='create':
			return ""
		else:
			return Statement.objects.filter().order_by('-add_time')

	def get_serializer_class(self):
		if self.action == "create":
			return CreateStatementSerializer
		elif self.action == 'update' or self.action == 'destroy':
			return ModiStatementSerializer
		else:
			return StatementSerializer

	@Core_connector()
	def retrieve(self, request, *args, **kwargs):
		code = kwargs.get('code', '')
		if not code:
			raise PubErrorCustom("对账编号为空！")
		instance = self.get_object()
		serializer=StatementSerializer(instance)
		serializer_detail=StatementDetailSerializer(StatementDetail.objects.filter(code=code).order_by('-add_time'), many=True)
		return {"data":{'title':serializer.data,'detail':serializer_detail.data}}

	@Core_connector(transaction=True)
	def destroy(self, request, *args, **kwargs):
		codes=request.data.get('codes', [])
		if not len(codes):
			raise PubErrorCustom("请选择要删除的记录！")
		objects=Statement.objects.filter(code__in=codes)
		if not objects.exists():
			raise PubErrorCustom("无此账单！")
		else:
			for obj in objects:
				if obj.status in [3,4]:
					raise PubErrorCustom("请勿删除已发布的账单！")
				if obj.status==2:
					obj.status=1
					obj.save()
					StatementDetail.objects.filter(code=obj.code).update(status=1)
				else:
					obj.delete()
					StatementDetail.objects.filter(code=obj.code).delete()
		return []

	@list_route(methods=['PUT'])
	@Core_connector(transaction=True)
	def release(self, request, *args, **kwargs):
		codes = request.data.get('codes', [])
		if not len(codes):
			raise PubErrorCustom("请求列表空！")
		objects=Statement.objects.filter(code__in=codes)
		if objects.exists():
			for obj in objects:
				assert obj.status==1,'对账单[%s]状态有误！'%(obj.code)
				obj.status=2
				"""
					暂时没有财务确认交易，先加上自动处理财务确认逻辑
				"""
				obj.status=4
				obj.confirm_amount=obj.goods_total
				obj.confirm_commission=obj.commission_total
				obj.save()
		StatementDetail.objects.filter(code__in=codes).update(status=2)
		return []

	@list_route(methods=['PUT'])
	@Core_connector(transaction=True)
	def confirm(self, request, *args, **kwargs):
		code = request.data.get('code',"")
		confirm_remark = request.data.get('confirm_remark', "")
		confirm_amount = Decimal(request.data.get('confirm_amount', 0.0))

		assert code , '请选择对账记录！'
		assert confirm_amount, '请输入确认金额！'

		object=Statement.objects.filter(code=code)
		if object.exists():
			for obj in object:
				assert obj.status==2,'对账单[%s]状态有误！'%(obj.code)
				if obj.goods_total < confirm_amount:
					raise PubErrorCustom("确认金额大于对账金额！")
				obj.confirm_remark = confirm_remark
				obj.confirm_amount = confirm_amount
				obj.tax_money = obj.confirm_amount * Decimal('0.16')
				obj.taxfree_money = obj.confirm_amount - obj.tax_money
				obj.total_money = obj.tax_money + obj.taxfree_money
				obj.status = 4
				obj.save()
				StatementDetail.objects.filter(code=obj.code).update(status=4)
		else:
			raise AssertionError("对账单[%s]记录不存在！"%(obj.code))
		return []
			
# 客户开票
class TicketViewset(GenericViewSetCustom):
	authentication_classes = [AdminUserAuthentication]
	filters_custom = [
	    {'key': "date", 'condition': "gte", 'inkey': 'start_dt' },
	    {'key': "date", 'condition': "lte", 'inkey': 'end_dt'},
	    {'key': "guest_company_name", 'all_query':True,},
	    {'key': 'order_code','condition':'like'},
	    {'key':'tax_number','condition':'like',},
	    {'key':'title','conditino':'like'}
	]
	lookup_field = ('pk')

	def inside_query_order(self,where_sql,params):
	
	    where_sql += ' order by t1.add_time desc'
	    print(params)
	    print(where_sql)
	    t1 = time.time()
	    orders = CustomOrder.objects.using('order').raw(
	        """SELECT t1.id as orderdetail_ptr_id,t1.*,t2.`id` as `order_sn`,t3.`id` as `receipt_id`,t3.`tax_number`,t3.`title`,t5.`returns_sn`,t4.status as order_operation_record_status,
	              t3.receipt_type,t3.company_address,t3.telephone,t3.bank,t3.account
	        FROM `order_detail` as t1
	          INNER JOIN  `order` as t2 on t1.`order`=t2.`id`
	          INNER JOIN  `receipt` as t3 on t2.`receipt` = t3.`id`
	          INNER JOIN  `order_operation_record` as t4 on t1.`son_order_sn` = t4.`order_sn`
	          INNER JOIN   (select  max(id) as id,order_sn,status from order_operation_record s where s.status in (6,14) group by  order_sn,status) as t6 on t4.id=t6.id
	          LEFT JOIN   `order_returns` as t5 on t1.`son_order_sn` = t5.`order_sn`
	
	        WHERE 1=1 and length(t3.`tax_number`)>0 {}""".format(where_sql), params)
	    orders = list(orders)
	    t2 = time.time()
	    print('数据库查询耗时:', t2 - t1)
	
	    return orders

	def inside_query_plan_order(self,where_sql,params):
		where_sql += ' order by t1.add_time desc'
		print(params)
		print(where_sql)
		t1 = time.time()
		plan_orders = CustomPlanOrder.objects.using('plan_order').raw(
		    """SELECT t1.id as planorder_ptr_id,t1.*,t3.`id` as `receipt_id`,t3.`tax_number`,t3.`title`,t1.status as order_operation_record_status,
		          t3.receipt_type,t3.company_address,t3.telephone,t3.bank,t3.account
		    FROM `plan_order` as t1
		      INNER JOIN  `receipt` as t3 on t1.`receipt_id` = t3.`id`
		    WHERE 1=1  and t1.status in (5,6,7) and length(t3.`tax_number`)>0 {}""".format(where_sql), params)
		plan_orders = list(plan_orders)
		t2 = time.time()
		print('数据库查询耗时:', t2 - t1)
		
		return plan_orders

	@Core_connector(pagination=True)
	def list(self, request, *args, **kwargs):
		is_type=self.request.query_params.get('is_type', '3')
		if str(is_type)=='1':
			params=[]
			where_sql= ' and t4.status in %s'
			params.append([6,14])
			orders = self.inside_query_order(where_sql=where_sql,params=params)
			plan_orders = self.inside_query_plan_order('', [])
	
			orders_codes=[]
			for item in orders :
				if item.order_operation_record_status == 6:
					orders_codes.append(item.son_order_sn )
				else:
					orders_codes.append(item.returns_sn)
			for item in plan_orders:
				orders_codes.append(item.plan_order_sn)
			Res_codes=[]
			F_res=FinanceReceiptListDetail.objects.filter(order_code__in=orders_codes)
			F_tmp=None
			if F_res.exists():
			    F_tmp=[ [item.order_code,item.receipt_id] for item in F_res ]
			if F_tmp:
			    F=FinanceReceipt.objects.filter(receipt_status=2,receipt_id__in=[ item[1] for item in F_tmp ] )
			    if F.exists():
			        F_tmp1=[ item.receipt_id for item in F ]
			        for item in F_tmp:
			            is_yes=False
			            for item1 in F_tmp1:
			                if item[1]==item1:
			                    is_yes=True
			            if not False:
			                Res_codes.append(item[0])
			
			res_orders=[]
			for item in orders:
			    is_yes=False
			    for r in Res_codes:
			        if item.order_operation_record_status == 6:
			            if item.son_order_sn==r:
			                is_yes=True
			        else:
			            if item.returns_sn==r:
			                is_yes=True
			    if not is_yes:
				    res_orders.append(item)
			res_plan_orders=[]
			for item in plan_orders:
				is_yes=False
				for r in Res_codes:
					if item.plan_order_sn==r:
						is_yes=True
				if not is_yes:
					res_plan_orders.append(item)
			
			data=NoFinanceReceiptPlanOrderSerializer(res_plan_orders,many=True).data+NoFinanceReceiptSerializer(res_orders,many=True).data
			
			return {"data":data}
		elif str(is_type)=='2':
		    detail=FinanceReceiptListDetail.objects.raw("""
		        SELECT t1.receipt_listdetailid as financereceiptlistdetail_ptr_id,t1.*,t2.receipt_sn,t2.receipt_no,t2.receipt_type
		        FROM  financereceiptlistdetail as t1
		        INNER JOIN financereceipt as t2  on t1.receipt_id=t2.receipt_id and t2.receipt_status=2
		        WHERE 1=1 order by t1.create_time desc
		    """)
		    detail=list(detail)
		    return {"data":FinanceReceiptDetailSerializer1(detail,many=True).data}
		else:
		    raise PubErrorCustom("is_type有误！")

	@Core_connector()
	def retrieve(self, request, *args, **kwargs):
	    pk = kwargs.get('pk', "")
	    assert pk, "发票编号空！"
	    class test():
	        def __init__(self,receipt_sn):
	            self.receipt_sn=receipt_sn
	    test=test(pk)
	    return {"data":FinanceReceiptDetailSerializer(test).data}

	@list_route(methods=['PUT'])
	@Core_connector(transaction=True)
	def ready(self, request, *args, **kwargs):
	    orders = request.data.get('orders', [])
	    if not len(orders):
	        raise PubErrorCustom( "请求列表空！")
	    TH=[]
	    DD=[]
	    FA=[]
	    for order in orders:
	        if str(order)[:2]=='DD':
	            DD.append(order)
	        elif str(order)[:2]=='TH':
	            TH.append(order)
	        elif str(order)[:2]=='FA':
	            FA.append(order)
	        else:
	            raise PubErrorCustom("类型有误！")
	    params = []
	    where_pan_sql=""
	    params_plan = []
	    where_sql = ' and t4.status in %s'
	    params.append([6, 14])
	    if len(TH):
	        where_sql += " and (t5.returns_sn in %s and t4.status='14')"
	        params.append(TH)
	    if len(DD):
	        if len(TH):
	            where_sql += " or (t1.son_order_sn in %s and t4.status='6')"
	            params.append(DD)
	        else:
	            where_sql += " and (t1.son_order_sn in %s and t4.status='6')"
	            params.append(DD)
	
	    if len(FA):
	        where_pan_sql +=  "  and t1.plan_order_sn in %s"
	        params_plan.append(FA)
	
	    title=None
	    title_object={}
	    goods_object=[]
	    goods_merge_object={}
	    finace_receipt=FinanceReceipt()
	    obj=[]
	    if len(DD) or len(TH):
	        obj+=NoFinanceReceiptSerializer1(self.inside_query_order(where_sql=where_sql, params=params),many=True).data
	    if len(FA):
	        obj+=NoFinanceReceiptPlanOrderDetailSerializer.data(request,self.inside_query_plan_order(where_sql=where_pan_sql,params=params_plan))
	    if not len(obj):
	        raise PubErrorCustom("请勾选数据！")
	    for item in obj:
	        if title:
	            if title!=item['title']:
	                raise PubErrorCustom("抬头不同！")
	        else:
	            finace_receipt.guest_company_name = item['guest_company_name']
	            finace_receipt.receipt_type = item['receipt_type']
	            finace_receipt.order_time = item['add_time']
	            finace_receipt.order_type = item['type']
	            finace_receipt.order_code = item['son_order_sn']
	            finace_receipt.goods_sn = item['goods_sn']
	            finace_receipt.goods_name = item['goods_name']
	            finace_receipt.model = item['model']
	            finace_receipt.receipt_title=item['title']
	            finace_receipt.receipt_addr=item['company_address']
	            finace_receipt.receipt_mobile=item['telephone']
	            finace_receipt.receipt_bank=item['bank']
	            finace_receipt.receipt_account=item['account']
	
	            title_object={
	                "title":item['title'],
	                'company_address':item['company_address'],
	                'telephone':item['telephone'],
	                'receipt_type':item['receipt_type'],
	                'receipt_sn':get_open_receipt_sn()['data']['open_receipt_sn'],
	                'tax_number':item['tax_number'],
	                'bank':item['bank'],
	                'account':item['account'],
	                'open_receipt_time':datetime_to_timestamp(get_time())
	            }
	        goods_object.append({
	            'order_code': item['son_order_sn'],
	            'goods_sn': item['goods_sn'],
	            'goods_name':item['goods_name'],
	            'model':item['model'],
	            'number':item['number'],
	            'unit':item['unit'],
	            'price':item['price'],
	            'amount':item['amount'],
	            'ticket_money':item['ticket_amount'],
	            'order_operation_record_status':item['order_operation_record_status'],
	            'reset_type': item['reset_type'] if 'reset_type' in item else '',
	            'order_time': finace_receipt.order_time,
	            'order_type': finace_receipt.order_type,
	            'guest_company_name': finace_receipt.guest_company_name ,
	        })
	        title=item['title']
	
	        if  not len(title_object) or not len(goods_object):
	            raise  PubErrorCustom("数据有误！")
	
	        finace_receipt.receipt_sn=title_object['receipt_sn']
	        finace_receipt.number = item['number']
	        finace_receipt.price = item['price']
	        finace_receipt.goods_money=0.0
	        finace_receipt.receipt_money=0.0
	
	    for goods in goods_object:
	        if 'reset_type' in goods and len(goods['reset_type']):
	            reset_type = goods['reset_type']+"mmmmmmmmmmmmmmmmmmmm"
	        else:
	            reset_type=goods['goods_name']+goods['model']
	        if reset_type not in goods_merge_object.keys():
	            goods_merge_object[reset_type]=dict()
	            tmp=goods_merge_object[reset_type]
	            tmp['goods_sn'] = goods['goods_sn']
	            if 'reset_type' in goods and len(goods['reset_type']):
	                tmp['goods_name']=goods['reset_type']
	            else:
	                tmp['goods_name'] = goods['goods_name']
	            tmp['goods_name1'] = goods['goods_name']
	            tmp['unit'] = goods['unit']
	            tmp['number'] = goods['number']
	            tmp['model'] = goods['model']
	            tmp['price'] = goods['price']
	            tmp['tax_rate1'] = Decimal ( 0.16 )
	            tmp['tax_rate'] = Decimal(16)
	            tmp['money'] = goods['ticket_money']
	        else:
	            tmp = goods_merge_object[reset_type]
	            if goods['order_operation_record_status'] == 6 or goods['order_code'][:2]=='FA':
	                tmp['number'] += goods['number']
	            else:
	                tmp['number'] -= goods['number']
	            tmp['money'] += goods['ticket_money']
	        finace_receipt.goods_money = Decimal (goods['amount']) + Decimal(finace_receipt.goods_money)
	        finace_receipt.receipt_money = Decimal(goods['ticket_money']) + Decimal(finace_receipt.receipt_money)
	
	    finace_receipt.save()
	
	    goods_merge_list = []
	    for key in goods_merge_object:
	        goods_merge=goods_merge_object[key]
	        tax=float_math.mul(abs(goods_merge['money']),goods_merge['tax_rate1'])
	        if  goods_merge['money']<0:
	            goods_merge['tax']   = Decimal(0.0)-tax
	            goods_merge['notax'] = Decimal(0.0)- (float_math.sub(abs(goods_merge['money']), tax))
	            goods_merge['ticket_money'] = goods_merge['notax'] + goods_merge['tax']
	        else:
	            goods_merge['notax'] = float_math.sub(goods_merge['money'], tax)
	            goods_merge['tax'] =  tax
	            goods_merge['ticket_money'] = goods_merge['notax'] + goods_merge['tax']
	
	        finace_receipt_list = FinanceReceiptList()
	        finace_receipt_list.receipt_id = finace_receipt.receipt_id
	        finace_receipt_list.receipt_sn =finace_receipt.receipt_sn
	        finace_receipt_list.goods_sn = goods_merge['goods_sn']
	        finace_receipt_list.goods_name = goods_merge['goods_name']
	        finace_receipt_list.model = goods_merge['model']
	        finace_receipt_list.unit = goods_merge['unit']
	        finace_receipt_list.number = goods_merge['number']
	        finace_receipt_list.price = goods_merge['price']
	        finace_receipt_list.rate = goods_merge['tax_rate']
	        finace_receipt_list.taxfree_money = goods_merge['notax']
	        finace_receipt_list.tax_money = goods_merge['tax']
	        finace_receipt_list.total_money = goods_merge['ticket_money']
	        finace_receipt_list.save()
	        goods_merge_list.append(goods_merge)
	
	    for goods in goods_object:
	        finace_receipt_list_detail = FinanceReceiptListDetail()
	        finace_receipt_list_detail.receipt_id=finace_receipt.receipt_id
	        finace_receipt_list_detail.receipt_listid=finace_receipt_list.receipt_listid
	        finace_receipt_list_detail.receipt_sn=finace_receipt.receipt_sn
	        finace_receipt_list_detail.order_code = goods['order_code']
	        finace_receipt_list_detail.goods_sn=goods['goods_sn']
	        finace_receipt_list_detail.goods_name = goods['goods_name']
	
	        finace_receipt_list_detail.model = goods['model']
	        finace_receipt_list_detail.unit = goods['unit']
	        finace_receipt_list_detail.number = goods['number']
	        finace_receipt_list_detail.price = goods['price']
	        finace_receipt_list_detail.goods_money = goods['amount']
	        finace_receipt_list_detail.receipt_money = goods['ticket_money']
	        finace_receipt_list_detail.order_type= goods['order_type']
	        finace_receipt_list_detail.order_time= goods['order_time']
	        finace_receipt_list_detail.guest_company_name=goods['guest_company_name']
	        finace_receipt_list_detail.save()
	
	    goods_merge_list=[ goods_merge_object[key] for key in goods_merge_object]
	
	    data={
	        'title':title_object,
	        'goods_list':goods_object,
	        'goods_merge':goods_merge_list,
	    }
	    return {"data":data}

	@list_route(methods=['PUT'])
	@Core_connector(transaction=True)
	def run(self,request, *args, **kwargs):
	    receipt_sn = request.data.get('receipt_sn')
	    receipt_no = request.data.get('receipt_no')
	    custom = request.data.get('custom')
	    addr = request.data.get('addr')
	    mobile = request.data.get('mobile')
	    img = request.data.get('receipt_url')
	    # if not receipt_no:
	    #     raise PubErrorCustom("发票号码为空！")
	    if not receipt_sn :
	        raise PubErrorCustom("发票编号为空！")
	    finance_receipt=FinanceReceipt.objects.filter(receipt_sn=receipt_sn)
	    if finance_receipt.exists():
	        finance_receipt=finance_receipt.first()
	
	        finance_receipt.receipt_status=2
	        finance_receipt.receipt_no=receipt_no
	        if custom:
	            finance_receipt.custom=custom
	        if addr:
	            finance_receipt.addr=addr
	        if mobile:
	            finance_receipt.mobile=mobile
	        if img:
	            finance_receipt.img = img
	        finance_receipt.save()
	    else:
	        raise  PubErrorCustom("该发票编号不存在！")
	    return {"data":[]}
	
	@list_route(methods=['GET'])
	@Core_connector()
	def all_guestname(self, request, *args, **kwargs):
		"""获取用户列表"""
		guest_info = set()
		order_details = OrderDetail.objects.using('order').filter()
		if order_details.exists():
			for order_detail in order_details:
				guest_info.add(order_detail.guest_company_name)
		plan_orders= PlanOrder.objects.using('plan_order').filter()
		if plan_orders.exists():
			for item in plan_orders:
				guest_info.add(item.guest_company_name)
		guest_info = list(guest_info)
		data = {
			'guest_info': guest_info
		}
		return {'data':data}

# 报表-交易明细
class TranListViewset(GenericViewSetCustom):
    authentication_classes = [AdminUserAuthentication]
    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def pay(self, request, *args, **kwargs):
        self.filters_custom = [
            {'key': "txn_time", 'condition': "gte", 'inkey': 'start_dt','func':datetime_to_timestamp, 'append': " 00:00:00"},
            {'key': "txn_time", 'condition': "lte", 'inkey': 'end_dt', 'func':datetime_to_timestamp,'append': ' 23:59:59'},
            {'key': 'guest_company_name', 'condition': 'like'},
            {'key': 'order_no', 'condition': 'like'},
            {'key': 'pay_status', },
        ]
        payment=CustomPayment.objects.using('payment').raw("""
            SELECT t1.id as payment_ptr_id,t1.*,t2.merchant_id,t2.unionpay_card
            FROM payment as t1
              INNER JOIN unionpay_records t2 ON t2.transaction_id=t1.transaction_id order by t1.txn_time desc
        """)
        payment=list(payment)
        orders1=[]
        for item in payment:
            orders1.append(item.order_no)
        orders=OrderDetail.objects.using('order').raw("""
                select t2.id as id,t1.`order_sn` ,t2.guest_company_name
                 from `order` as t1  inner join order_detail as  t2 on t1.id=t2.order
                 where t1.order_sn in %s """,[orders1])
        orders=list(orders)
        for item in orders:
            for item_inner in payment:
                if item.order_sn==item_inner.order_no:
                    item_inner.guest_company_name=item.guest_company_name

        orders = PlanOrder.objects.using('plan_order').raw("""
		        select t1.id ,t1.guest_company_name,t1.plan_order_sn,t2.plan_order_pay_sn
		         from `plan_order` as t1
		         inner join plan_order_payment as t2  on t1.plan_order_sn = t2.plan_order_sn
		         where t2.plan_order_pay_sn in %s""", [orders1])
        orders = list(orders)
        for item in orders:
            for item_inner in payment:
                if item.plan_order_pay_sn == item_inner.order_no:
	                item_inner.guest_company_name = item.guest_company_name
		
        return {"data":PayTranListSerializer(payment, many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def refund(self, request, *args, **kwargs):
        self.filters_custom = [
            {'key': "txn_time", 'condition': "gte", 'inkey': 'start_dt', 'func':datetime_to_timestamp,'append': " 00:00:00"},
            {'key': "txn_time", 'condition': "lte", 'inkey': 'end_dt','func':datetime_to_timestamp, 'append': ' 23:59:59'},
            {'key': 'guest_company_name', 'condition': 'like'},
            {'key': 'order_no', 'condition': 'like'},
            {'key': 'refund_status','inkey':'pay_status' },
        ]
        payment = CustomPayment.objects.using('payment').raw("""
             SELECT t1.id as payment_ptr_id,t1.*,t2.merchant_id,t2.unionpay_card
             FROM refund as t1
               INNER JOIN unionpay_records t2 ON t2.transaction_id=t1.transaction_id order by t1.txn_time desc
         """)
        payment = list(payment)
        orders1 = []
        for item in payment:
            orders1.append(item.order_no)
        orders = CustomOrder.objects.using('order').raw("""
                 select t1.id as orderdetail_ptr_id,t1.son_order_sn as son_order_sn ,t1.guest_company_name , t3.`order_sn` as link_order_sn
                  from `order_detail` as t1
                      inner join `order` as t3 on t1.order=t3.id
                  where t1.son_order_sn in %s """, [orders1])
        orders = list(orders)
        for item in orders:
            for item_inner in payment:
                if item.son_order_sn == item_inner.order_no:
                    item_inner.guest_company_name = item.guest_company_name
                    item_inner.link_order_sn = item.link_order_sn

        orders = PlanOrder.objects.using('plan_order').raw("""
                 select t1.id ,t1.plan_order_sn as son_order_sn ,t1.guest_company_name , t1.`plan_sn` as link_order_sn,t2.plan_order_pay_sn
                  from `plan_order` as t1
                  inner join plan_order_payment as t2  on t1.plan_order_sn = t2.plan_order_sn
                  where t2.plan_order_pay_sn in %s """, [orders1])
        orders = list(orders)
        for item in orders:
            for item_inner in payment:
                if item.plan_order_pay_sn == item_inner.order_no:
                    item_inner.guest_company_name = item.guest_company_name
                    item_inner.link_order_sn = item.link_order_sn
        return {"data":RefundPayTranListSerializer(payment, many=True).data}

# 报表-对账查询
class StatementDetaiExlViewset(GenericViewSetCustom):
	authentication_classes = [AdminUserAuthentication]

	@list_route(methods=['GET'])
	@Core_connector(pagination=True)
	def statement(self, request, *args, **kwargs):
		self.filters_custom = [
			{'key': "supplier_id"},
			{'key': "order_code", 'condition': 'like', },
			{'key': "limit_filter", 'condition': "gte", 'inkey': 'start_dt'},
			{'key': "limit_filter", 'condition': "lte", 'inkey': 'end_dt'},
			{'key': "code", 'condition': 'like', },
		]
		obj = StatementDetail.objects.raw(
			"""
                select t1.id as statementdetail_ptr_id,
                      t1.*,t2.limit,t2.status as main_status
                from statementdetail as t1
                inner join statement as t2 on t1.code=t2.code
                where t1.status=3 order by t1.add_time desc
            """
		)

		data = StatementDetailExSerializer(obj, many=True).data

		header = {
			"number_tot": reduce(lambda x, y: int(x) + int(y['number']), data, 0),
			"amount": reduce(lambda x, y: Decimal(x) + Decimal(y['amount']), data, 0),
			"commission": reduce(lambda x, y: Decimal(x) + Decimal(y['commission']), data, 0),
		}

		return {"data": data, 'header': header}

	@list_route(methods=['GET'])
	@Core_connector(pagination=True)
	def unstatement(self, request, *args, **kwargs):
		self.filters_custom = [
			{'key': "supplier_id"},
			{'key': "order_code", 'condition': 'like', },
			{'key': "order_date", 'condition': "gte", 'inkey': 'start_dt'},
			{'key': "order_date", 'condition': "lte", 'inkey': 'end_dt'},
		]
		# 获取满足条件订单(含普通订单和方案订单)
		supplier = OrderAllQuery.get_supplier()
		DD_params = [supplier]
		FA_params = [supplier]
		TH_params = [supplier]
		if not len(supplier):
			return []
		obj, obj_FA = get_orders_obj(FA_flag=True, DD_flag=True, TH_flag=True,
									 DD_where_sql=" and t1.supplier_id in %s",
									 TH_where_sql=" and t1.supplier_id in %s",
									 FA_where_sql=" and t1.supplier_id in %s",
									 DD_params=DD_params, TH_params=TH_params, FA_params=FA_params,
									 DD_status=[7], TH_status=[14], FA_status=[6, 7])
		statement_list = obj + obj_FA
		statement_list.sort(key=lambda x: x.add_time, reverse=True)
		data = []

		orders = [item.order_code for item in statement_list]
		obj = StatementDetail.objects.filter(use_code__in=orders, status=3)
		if obj.exists():
			for item in obj:
				if item.use_code in orders:
					orders.remove(item.use_code)
		statement_list_tmp = []
		for obj in statement_list:
			isFlag = False
			for item in orders:
				if item == obj.order_code:
					isFlag = True
					break
			if isFlag:
				statement_list_tmp.append(obj)

		for item in statement_list_tmp:
			data.append({
				'supplier_id': item.supplier_id,
				'supplier_name': item.supplier_name if item.supplier_name else '',
				'order_date': item.add_time.date(),
				'type': '退货单' if item.order_code[:2] == 'TH' else '订单',
				'order_code': item.order_code,
				'goods_name': item.goods_name,
				'model': item.model,
				'price': item.price,
				'number': item.number,
				'amount': Decimal(0.0) - item.use_pay_total if item.order_code[:2] == 'TH' else item.use_pay_total,
				'commission': Decimal(0.0) - item.use_commission if item.order_code[
																	:2] == 'TH' else item.use_commission,
			})
		header = {
			"number_tot": reduce(lambda x, y: int(x) + int(y['number']), data, 0),
			"amount": reduce(lambda x, y: Decimal(x) + Decimal(y['amount']), data, 0),
			"commission": reduce(lambda x, y: Decimal(x) + Decimal(y['commission']), data, 0),
		}

		return {"data": data, 'header': header}

#  资源下载
class MediaExport(GenericViewSetCustom):
    def retrieve(self,request, *args, **kwargs):
        filename = kwargs.get('pk')
        filename= "%s.xlsx"%filename
        file_path = os.path.join(os.path.abspath('media'), filename)

        with open(file_path, 'rb') as f:
            file_stream = f.read()
        os.remove(file_path)
        from django.http import HttpResponse
        response = HttpResponse(file_stream)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{}"'.format(filename)
        return response

