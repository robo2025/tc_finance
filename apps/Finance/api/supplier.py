
from rest_framework.decorators import detail_route, list_route
from core.decorator.response import Core_connector
from auth.authentication import SupplierAuthentication
from utils.exceptions import PubErrorCustom

from apps.Finance.Custom.mixins import (ListModelMixinCustom, GenericViewSetCustom)
from apps.Finance.Custom.serializers import StatementSerializer,StatementDetailSerializer,OrderAllQuery,StatementDetailExSerializer
from apps.Finance.models import Statement,StatementDetail

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
                assert obj.status == 3, '对账单[%s]状态有误！' % (obj.code)
                obj.status = 4
                obj.save()
                StatementDetail.objects.filter(code=obj.code).update(status=4)
        else:
            raise AssertionError("对账单[%s]记录不存在！" % (obj.code))
        return []

# 报表-对账查询
class StatementSupDetaiExlViewset(GenericViewSetCustom):
    authentication_classes = [SupplierAuthentication]
    filters_custom = [
        {'key': "supplier_id"},
        {'key': "order_code"},
        {'key': "date", 'condition': "gte", 'inkey': 'start_dt'},
        {'key': "date", 'condition': "lte", 'inkey': 'end_dt'},
    ]
    def get_serializer_class(self):
        return StatementDetailExSerializer

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def statement(self, request, *args, **kwargs):
            return {"data":self.get_serializer(StatementDetail.objects.filter(status=4).order_by('-add_time'), many=True).data}

    @list_route(methods=['GET'])
    @Core_connector(pagination=True)
    def unstatement(self, request, *args, **kwargs):
        # 获取满足条件订单(含普通订单和方案订单)
        supplier=OrderAllQuery.get_supplier()
        if not len(supplier):
            return []
        statement_list = OrderAllQuery.query( \
                                status=(7, 14),
                                plan_status=(6, 7),
                                supplier=tuple(supplier))
        data=[]
        from decimal import Decimal
        for item in statement_list:
            if  StatementDetail.objects.filter(order_code=item['order_code'],status=4).exists():
                continue
            data.append({
                'supplier_id':item['supplier_id'],
                'supplier_name':item['supplier_name'],
                'order_date':item['order_date'],
                'type':'订单' if item['status']==7 else '退款单',
                'order_code' : item['order_code'],
                'goods_name' : item['goods_name'],
                'model':item['model'],
                'price':item['price'],
                'number':item['number'],
                'amount':item['price']*item['number'] if item['status']==7 else Decimal(0.00)-(item['price']*item['number']),
                 'commission':item['commission'] if item['status']==7 else Decimal(0.00)-item['commission'],
            })
        return {"data":data}