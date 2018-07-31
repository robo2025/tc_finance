from rest_framework.decorators import detail_route, list_routefrom core.decorator.response import Core_connectorfrom utils.exceptions import PubErrorCustomfrom auth.authentication import AdminUserAuthenticationfrom apps.Finance.Custom.mixins import (                    GenericViewSetCustom)from apps.Finance.plan_model import PlanOrderfrom apps.Finance.order_model import OrderDetailfrom apps.Finance.models import (					FReceiptListDetail,					FReceiptList,					FReceipt)from apps.Finance.Custom.serializers import (					NoFRceiptSerializer,					YesFRceiptSerializer,					FReceiptListDetailSerializer,					FReceiptListSerializer,					FReceiptSerializer,					FINReceiptListDetailSerializer,					FINReceiptListSerializer,					FINReceiptSerializer,					NoFinanceReceiptSerializer,					FinanceReceiptDetailSerializer1,					FinanceReceiptDetailSerializer)from apps.Finance.utils import (					set_receiptl_info,					noticket_query,					yesticket_query,					nogoodsticket_query,					get_FA_DD_TH,					run_FA_DD_TH,					receipt_confirm_ex,					yesgoodsticket_query,                    get_orders_obj)class CommissionTicket(GenericViewSetCustom):	filters_custom = [	    {'key': "filter_date", 'condition': "gte", 'inkey': 'start_dt' },	    {'key': "filter_date", 'condition': "lte", 'inkey': 'end_dt'},	    {'key': "supplier_id", 'all_query':True,},	    {'key': 'code','condition':'like'},	]	@Core_connector(pagination=True)	def list(self,request):		is_type = self.request.query_params.get('is_type', '3')		if str(is_type)=='1':			return {'data': NoFRceiptSerializer(noticket_query(), many=True).data}		elif str(is_type)=='2':			return {'data': YesFRceiptSerializer(yesticket_query(), many=True).data}		else:		    raise PubErrorCustom("is_type有误！")		@Core_connector()	def retrieve(self,request,*args,**kwargs):		receipt_sn = kwargs.get('pk', None)		if not receipt_sn :			raise PubErrorCustom("发票编号为空！")		if not isinstance(receipt_sn, str):			raise PubErrorCustom("发票编号有误！")		receipt=FReceipt.objects.filter(receipt_sn=receipt_sn, receipt_status=2)		if not receipt.exists():			raise PubErrorCustom("此发票无开票数据！")		return {'data':{			"title":FReceiptSerializer(receipt[0],many=False).data,			'goods_merge':FReceiptListSerializer(FReceiptList.objects.filter(receipt_sn=receipt_sn,status=2),many=True).data,			'goods':FReceiptListDetailSerializer(FReceiptListDetail.objects.filter(receipt_sn=receipt_sn,status=2),many=True).data		}}		@list_route(methods=['PUT'])	@Core_connector(transaction=True)	def ready(self, request):		orders = self.request.data.get('orders', None)		if not orders:			raise PubErrorCustom("订单号为空！")				orders_obj = dict()		obj = noticket_query(" and t1.use_code in %s", [orders])		for item in obj:			item.unit = '台'			item.rest_type = item.goods_sn + item.model			orders_obj[item.use_code] = item		if not orders_obj or len(orders_obj) < len(orders):			raise PubErrorCustom("选择的开票信息有误，请重新选择！")				FA, DD, TH = run_FA_DD_TH(orders)		for obj in FA:			orders_obj[obj.order_code].receipt = obj		for obj in DD:			orders_obj[obj.order_code].receipt = obj		for obj in TH:			orders_obj[obj.order_code].receipt = obj				data=set_receiptl_info(request, orders_obj)		return { 'data':{			'title': FReceiptSerializer(data['title'], many=False).data,			'goods_merge': FReceiptListSerializer(data['goods_merge'], many=True).data,			'goods': FReceiptListDetailSerializer(data['goods'], many=True).data,			}		}	@list_route(methods=['PUT'])	@Core_connector(transaction=True)	def run(self,request):		receipt_sn = request.data.get('receipt_sn',"")		if not receipt_sn:			raise PubErrorCustom("发票编号为空！")				finance_receipt = FReceipt.objects.filter(receipt_sn=receipt_sn)		if not finance_receipt.exists():			raise PubErrorCustom("该发票编号不存在！")		else:			finance_receipt = finance_receipt.first()			receipt_no = request.data.get('receipt_no', "")			custom = request.data.get('custom', "")			addr = request.data.get('addr', "")			mobile = request.data.get('mobile', "")			img = request.data.get('img', "")			finance_receipt.receipt_status = 2			finance_receipt.receipt_no = receipt_no			if custom:				finance_receipt.custom = custom			if addr:				finance_receipt.addr = addr			if mobile:				finance_receipt.mobile = mobile			if img:				finance_receipt.img = img			finance_receipt.save()		return {"data": []}	class CommissionTicketQuery(GenericViewSetCustom):		@list_route(methods=['GET'])	@Core_connector(pagination=True)	def no(self,request):		return {'data': NoFRceiptSerializer(noticket_query(), many=True).data}		@list_route(methods=['GET'])	@Core_connector(pagination=True)	def yes(self,request):		return {'data': YesFRceiptSerializer(yesticket_query(), many=True).data}class TicketViewset(GenericViewSetCustom):    authentication_classes = [AdminUserAuthentication]    filters_custom = [        {'key': "date", 'condition': "gte", 'inkey': 'start_dt' },        {'key': "date", 'condition': "lte", 'inkey': 'end_dt'},        {'key': "guest_company_name", 'all_query':True,},        {'key': 'order_code','condition':'like'},        {'key':'tax_number','condition':'like',},        {'key':'title','conditino':'like'}    ]    @Core_connector(pagination=True)    def list(self, request):        is_type = self.request.query_params.get('is_type', '3')        if str(is_type) == '1':            obj, obj_FA = get_orders_obj(FA_flag=True, DD_flag=True, TH_flag=True, DD_status=[6], TH_status=[14], FA_status=[5, 6, 7],FA_params=[],DD_params=[],TH_params=[])            return {'data': NoFinanceReceiptSerializer(nogoodsticket_query(obj,obj_FA), many=True).data}        elif str(is_type) == '2':            return {'data': FinanceReceiptDetailSerializer1(yesgoodsticket_query(), many=True).data}        else:            raise PubErrorCustom("is_type有误！")    @Core_connector()    def retrieve(self, request, *args, **kwargs):        pk = kwargs.get('pk', "")        assert pk, "发票编号空！"        class test():            def __init__(self,receipt_sn):                self.receipt_sn=receipt_sn        test=test(pk)        data=FinanceReceiptDetailSerializer(test).data        if not len(data['goods_list']):            data.pop('goods_list')        return {"data":data}    @list_route(methods=['PUT'])    @Core_connector(transaction=True)    def ready(self, request):        orders = self.request.data.get('orders', None)        if not orders:            raise PubErrorCustom("订单号为空！")        FA, DD, TH=get_FA_DD_TH(orders)        if not len(FA) and not len(DD) and not len(TH):            raise PubErrorCustom("请勾选订单！")        if (len(FA) and (len(DD) or len(TH))) or (len(FA)>1):            raise PubErrorCustom("方案订单只能单订单开票！")        FA_where_sql=""        FA_params=[]        FA_flag=False        DD_where_sql=""        DD_params=[]        DD_flag=False        TH_where_sql=""        TH_params=[]        TH_flag=False        if len(FA):            FA_where_sql+=" and t1.plan_order_sn in %s"            FA_params.append(FA)            FA_flag=True        if len(DD):            DD_where_sql += " and t1.son_order_sn in %s"            DD_params.append(DD)            DD_flag=True        if len(TH):            TH_where_sql += " and t5.returns_sn in %s"            TH_params.append(TH)            TH_flag=True        order_obj,order_obj_FA=get_orders_obj(FA_flag=FA_flag,DD_flag=DD_flag,TH_flag=TH_flag,FA_where_sql=FA_where_sql,FA_params=FA_params,DD_where_sql=DD_where_sql,DD_params=DD_params,TH_where_sql=TH_where_sql,TH_params=TH_params)        data = set_receiptl_info(request, nogoodsticket_query(order_obj,order_obj_FA),1)        if not FA:            return {'data': {                'title': FINReceiptSerializer(data['title'], many=False).data,                'goods_merge': FINReceiptListSerializer(data['goods_merge'], many=True).data,                'goods_list': FINReceiptListDetailSerializer(data['goods'], many=True).data,}            }        else:            return {'data': {                'title': FINReceiptSerializer(data['title'], many=False).data,                'goods_merge': FINReceiptListSerializer(data['goods_merge'], many=True).data,}            }    @list_route(methods=['PUT'])    @Core_connector(transaction=True)    def run(self, request):        receipt_confirm_ex(request)        return {"data": []}    @list_route(methods=['GET'])    @Core_connector()    def all_guestname(self, request, *args, **kwargs):        """获取用户列表"""        guest_info = set()        order_details = OrderDetail.objects.using('order').filter()        if order_details.exists():            for order_detail in order_details:                guest_info.add(order_detail.guest_company_name)        plan_orders= PlanOrder.objects.using('plan_order').filter()        if plan_orders.exists():            for item in plan_orders:                guest_info.add(item.guest_company_name)        guest_info = list(guest_info)        data = {            'guest_info': guest_info        }        return {'data':data}