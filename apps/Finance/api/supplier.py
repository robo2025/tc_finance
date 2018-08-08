
from decimal import Decimal
from rest_framework.decorators import detail_route, list_route
from core.decorator.response import Core_connector
from auth.authentication import SupplierAuthentication
from utils.exceptions import PubErrorCustom

from apps.Finance.Custom.mixins import (ListModelMixinCustom, GenericViewSetCustom)
from apps.Finance.Custom.serializers import (StatementSerializer,StatementDetailSerializer,
                                                OrderAllQuery,StatementDetailExSerializer,NoFRceiptSerializer,
                                             YesFRceiptSerializer,StatementTicketSerializer,SettlementListSupCommissionSerializer,
                                                StatementDetailSerializer1,SettlementListSupSerializer,SettlementListPaySupSerializer)
from apps.Finance.models import Statement,StatementDetail

from apps.Finance.utils import get_orders_obj,noticket_query,yesticket_query,SettlementHandleGoods,SettlementHandleCommission

class StatementSupViewset(ListModelMixinCustom,GenericViewSetCustom):

    authentication_classes = [SupplierAuthentication]
    filters_custom =[
        {'key': "limit", 'condition': "gte", 'inkey': 'start_ym' ,'func' :lambda x :x.replace('-' ,'')},
        {'key': "limit", 'condition': "lte", 'inkey': 'end_ym' ,'func' :lambda x :x.replace('-' ,'')},
        {'key': "status" ,},
        {'key': "supplier_id", 'all_query': True},
    ]
    lookup_field = ("code")

    def get_queryset(self):
        return Statement.objects.filter(supplier_id=self.request.user.main_user_id).order_by('-add_time')

    def get_serializer_class(self):
        return StatementSerializer

    @Core_connector()
    def retrieve(self, request, *args, **kwargs):
        code = kwargs.get('code', '')
        if not code:
            raise PubErrorCustom("对账编号为空！")
        instance = self.get_object()
        serializer = StatementSerializer(instance)
        serializer_detail = StatementDetailSerializer(StatementDetail.objects.filter(code=code).order_by('-add_time'),
                                                      many=True)
        return {"data": {'title': serializer.data, 'detail': serializer_detail.data}}

    @list_route(methods=['PUT'])
    @Core_connector(transaction=True)
    def confirm(self, request, *args, **kwargs):
        code = request.data.get('code', "")
        assert code, '请选择对账记录！'

        object = Statement.objects.filter(code=code)
        if object.exists():
            for obj in object:
                assert obj.status == 4, '对账单[%s]状态有误！' % (obj.code)
                obj.status = 3
                obj.save()
                StatementDetail.objects.filter(code=obj.code).update(status=3)
        else:
            raise AssertionError("对账单[%s]记录不存在！" % (obj.code))
        return []

class TicketUploadViewset(GenericViewSetCustom):

    authentication_classes = [SupplierAuthentication]

    @Core_connector(pagination=True)
    def list(self,request,*args,**kwargs):
        is_type=self.request.query_params.get('is_type',None)
        start_ym=self.request.query_params.get('start_ym',None)
        end_ym=self.request.query_params.get('end_ym',None)

        statement_queryset=Statement.objects.all()

        if is_type and str(is_type)=='1':
            statement_queryset=statement_queryset.filter(img_url='')
        elif is_type and str(is_type)=='2':
            statement_queryset=statement_queryset.exclude(img_url='')

        if start_ym and end_ym and start_ym <= end_ym:
            start_ym=start_ym.replace('-')
            end_ym=end_ym.replace('-')
            statement_queryset=statement_queryset.filter(limit__gte=start_ym,limit__lte=end_ym)

        return {'data':StatementTicketSerializer(statement_queryset.filter(status=3),many=True).data}

    @Core_connector(transaction=True)
    def update(self,request,*args,**kwargs):
        pk=kwargs.get('pk',None)
        img_url=self.request.data.get('img_url',None)
        if pk and img_url:
            isinstance=Statement.objects.filter(code=pk)
            if not isinstance:
                raise PubErrorCustom("未找到")
            isinstance.update(img_url=img_url)
        return []

class StatementSupDetaiExlViewset(GenericViewSetCustom):
    authentication_classes = [SupplierAuthentication]

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

        obj=StatementDetail.objects.raw(
            """
                select t1.id as statementdetail_ptr_id,
                      t1.*,t2.limit,t2.status as main_status
                from statementdetail as t1
                inner join statement as t2 on t1.code=t2.code
                where t2.supplier_id=%s and t1.status=3 order by t1.add_time desc
            """,[self.request.user.main_user_id]
        )
        return {"data":StatementDetailExSerializer(obj, many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def unstatement(self, request, *args, **kwargs):
        self.filters_custom = [
            {'key': "supplier_id"},
            {'key': "order_code",'condition':'like',},
            {'key': "order_date", 'condition': "gte", 'inkey': 'start_dt'},
            {'key': "order_date", 'condition': "lte", 'inkey': 'end_dt'},
        ]
        # 获取满足条件订单(含普通订单和方案订单)
        supplier=[self.request.user.main_user_id]
        supplier=OrderAllQuery.get_supplier(supplier)
        DD_params=[supplier]
        FA_params=[supplier]
        TH_params=[supplier]
        if not len(supplier):
            return []
        obj,obj_FA = get_orders_obj(FA_flag=True,DD_flag=True,TH_flag=True,
                                                DD_where_sql=" and t1.supplier_id in %s",
                                                TH_where_sql=" and t1.supplier_id in %s",
                                                FA_where_sql=" and t1.supplier_id in %s",
                                                DD_params=DD_params,TH_params=TH_params,FA_params=FA_params,
                                                DD_status=[7],TH_status=[14],FA_status=[6,7])
        statement_list=obj+obj_FA
        statement_list.sort(key=lambda x: x.add_time, reverse=True)
        data=[]

        orders= [ item.order_code for item in statement_list ]
        obj=StatementDetail.objects.filter(use_code__in=orders, status=3)
        if obj.exists():
            for item in obj:
                if item.use_code in orders:
                    orders.remove(item.use_code)
        statement_list_tmp=[]
        for obj in statement_list:
            isFlag=False
            for item in orders:
                if item == obj.order_code :
                    isFlag=True
                    break
            if isFlag:
                statement_list_tmp.append(obj)

        for item in statement_list_tmp:
            data.append({
                'supplier_id':item.supplier_id,
                'supplier_name':item.supplier_name if item.supplier_name else '',
                'order_date':item.add_time.date(),
                'type':'退货单' if item.order_code[:2]=='TH' else '订单',
                'order_code' : item.order_code,
                'goods_name' : item.goods_name,
                'model':item.model,
                'price':item.price,
                'number':item.number,
                'amount':Decimal(0.0) - item.use_pay_total if item.order_code[:2]=='TH' else item.use_pay_total,
                 'commission':Decimal(0.0) - item.use_commission if item.order_code[:2]=='TH' else item.use_commission,
            })
        return {"data":data}

class CommissionSupTicket(GenericViewSetCustom):
    authentication_classes = [SupplierAuthentication]

    @Core_connector(pagination=True)
    def list(self,request):
        is_type = self.request.query_params.get('is_type', '3')
        if str(is_type) != '1' and str(is_type) != '2':
            raise PubErrorCustom("is_type有误！")

        where_sql = str()
        params = list()
        code = self.request.query_params.get('code', None)
        supplier_id = self.request.query_params.get('supplier_id', None)
        start_dt = self.request.query_params.get('start_dt', None)
        end_dt = self.request.query_params.get('end_dt', None)
        order_code = self.request.query_params.get('order_code', None)
        limit = self.request.query_params.get('ym', None)
        start_limit = self.request.query_params.get('start_ym', None)
        end_limit = self.request.query_params.get('end_ym', None)
        if code:
            where_sql = "{} and LOCATE(%s,t2.code)>0".format(where_sql)
            params.append(code)
        if order_code:
            where_sql = "{} and LOCATE(%s,t1.use_code)>0".format(where_sql)
            params.append(order_code)
        if limit :
            limit=limit.replace('-','')
            where_sql = "{} and t2.limit=%s".format(where_sql)
            params.append(limit)
        if supplier_id and str(supplier_id) != 'all' and str(supplier_id) != '0':
            where_sql = "{} and t2.supplier_id = %s".format(where_sql)
            params.append(supplier_id)
        if start_dt and end_dt and end_dt >= start_dt:
            where_sql = "{} and ( (substr(t1.use_code,1,2)='FA' and t1.refund_date >= %s  and t1.refund_date <= %s ) or  \
                           (substr(t1.use_code,1,2)!='FA' and t1.order_date >= %s  and t1.order_date <= %s )  )".format(
                where_sql)
            params.append(start_dt)
            params.append(end_dt)
            params.append(start_dt)
            params.append(end_dt)
        if start_limit and end_limit and end_limit >= start_limit:
            start_limit=start_limit.replace('-','')
            end_limit=end_limit.replace('-','')
            where_sql = "{} and t2.limit >=%s and t2.limit <=%s ".format(where_sql)
            params.append(start_limit)
            params.append(end_limit)

        if str(is_type)=='1':
             return {'data': NoFRceiptSerializer(noticket_query(where_sql=where_sql,params=params), many=True).data}
        elif str(is_type)=='2':
            return {'data': YesFRceiptSerializer(yesticket_query(where_sql=where_sql,params=params), many=True).data}

class SettlementSupViewset(GenericViewSetCustom,SettlementHandleGoods):

    @Core_connector(pagination=True)
    def list(self,request,*args,**kwargs):
        where_sql=str()
        params=list()

        start_ym=self.request.query_params.get('start_ym',None)
        end_ym=self.request.query_params.get('end_ym',None)
        code = self.request.query_params.get('code',None)

        if code:
            where_sql = "{} and LOCATE(%s,t1.code)>0".format(where_sql)
            params.append(code)
        if start_ym and end_ym and end_ym >= start_ym:
            start_ym = start_ym.replace('-', '')
            end_ym = end_ym.replace('-', '')
            where_sql = "{} and t1.limit >=%s and t1.limit <=%s ".format(where_sql)
            params.append(start_ym)
            params.append(end_ym)

        self.query(where_sql,params)
        return {'data':SettlementListSupSerializer(self.data,many=True).data}

    @Core_connector()
    def retrieve(self, request, *args, **kwargs):
        return {'data':StatementDetailSerializer1(StatementDetail.objects.filter(code=kwargs.get('pk')).order_by('-order_date'),many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def paylist(self,request,*args,**kwargs):
        where_sql=str()
        params=list()

        start_dt=self.request.query_params.get('start_dt',None)
        end_dt=self.request.query_params.get('end_dt',None)

        if start_dt and end_dt and end_dt >= start_dt:
            where_sql = "{} and substr(t1.create_time,1,10) >=%s and substr(t1.create_time,1,10) <=%s ".format(where_sql)
            params.append(start_dt)
            params.append(end_dt)

        self.payquery(where_sql,params)
        return {'data':SettlementListPaySupSerializer(self.data,many=True).data}

class SettlementCommissionSupViewset(GenericViewSetCustom,SettlementHandleCommission):

    @Core_connector(pagination=True)
    def list(self, request, *args, **kwargs):
        where_sql = str()
        params = list()

        start_ym = self.request.query_params.get('start_ym', None)
        end_ym = self.request.query_params.get('end_ym', None)
        code = self.request.query_params.get('code', None)

        if code:
            where_sql = "{} and LOCATE(%s,t1.code)>0".format(where_sql)
            params.append(code)
        if start_ym and end_ym and end_ym >= start_ym:
            start_ym = start_ym.replace('-', '')
            end_ym = end_ym.replace('-', '')
            where_sql = "{} and t1.limit >=%s and t1.limit <=%s ".format(where_sql)
            params.append(start_ym)
            params.append(end_ym)

        self.query(where_sql, params)
        return {'data': SettlementListSupCommissionSerializer(self.data, many=True).data}

    @Core_connector(transaction=True)
    def create(self,request,*args,**kwargs):
        self.settlement(self.request.data)
        return []

    @Core_connector()
    def retrieve(self, request, *args, **kwargs):
        return {'data':StatementDetailSerializer1(StatementDetail.objects.filter(code=kwargs.get('pk')).order_by('-order_date'),many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def paylist(self,request,*args,**kwargs):
        where_sql=str()
        params=list()

        start_dt=self.request.query_params.get('start_dt',None)
        end_dt=self.request.query_params.get('end_dt',None)

        if start_dt and end_dt and end_dt >= start_dt:
            where_sql = "{} and substr(t1.create_time,1,10) >=%s and substr(t1.create_time,1,10) <=%s ".format(where_sql)
            params.append(start_dt)
            params.append(end_dt)

        self.payquery(where_sql,params)
        return {'data':SettlementListPaySupSerializer(self.data,many=True).data}