
from decimal import Decimal
from rest_framework.decorators import detail_route, list_route
from core.decorator.response import Core_connector
from auth.authentication import SupplierAuthentication
from utils.exceptions import PubErrorCustom

from apps.Finance.Custom.mixins import (ListModelMixinCustom, GenericViewSetCustom)
from apps.Finance.Custom.serializers import StatementSerializer,StatementDetailSerializer,OrderAllQuery,StatementDetailExSerializer
from apps.Finance.models import Statement,StatementDetail

from apps.Finance.utils import get_orders_obj

# 对账单
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
        return Statement.objects.filter().order_by('-add_time')

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
                assert obj.status == 2, '对账单[%s]状态有误！' % (obj.code)
                obj.status = 3
                obj.save()
                StatementDetail.objects.filter(code=obj.code).update(status=3)
        else:
            raise AssertionError("对账单[%s]记录不存在！" % (obj.code))
        return []

# 报表-对账查询
class StatementSupDetaiExlViewset(GenericViewSetCustom):
    authentication_classes = [SupplierAuthentication]

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def statement(self, request, *args, **kwargs):
        self.filters_custom = [
            {'key': "supplier_id"},
            {'key': "order_code", 'condition': 'like', },
            {'key': "limit", 'condition': "gte", 'inkey': 'start_dt'},
            {'key': "limit", 'condition': "lte", 'inkey': 'end_dt'},
            {'key': "code", 'condition': 'like', },
        ]
        obj=StatementDetail.objects.raw(
            """
                select t1.id as statementdetail_ptr_id,
                      t1.*,t2.limit,t2.status as main_status
                from statementdetail as t1
                inner join statement as t2 on t1.code=t2.code
                where t1.status=3 order by t1.add_time desc
            """
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
        supplier=OrderAllQuery.get_supplier()
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