
from django.urls import path, include
from rest_framework.routers import DefaultRouter, Route
from rest_framework.documentation import include_docs_urls

from Finance.api.api1 import (  PriceruleViewSet,
                                RefundOrderViewSet,
                                StatementViewset,
                                # TicketViewset,
                                StatementDetaiExlViewset,
                                TranListViewset,
                                MediaExport)

from Finance.api.api2 import ( CommissionTicket,TicketViewset,AccTermRuleViewset,AccTermActionViewset,SettlementViewset,SettlementCommissionViewset)

from Finance.api.supplier import StatementSupViewset,StatementSupDetaiExlViewset,CommissionSupTicket,TicketUploadViewset,SettlementSupViewset,SettlementCommissionSupViewset,TicketSupViewset

route_urls=[
    # 结算价格规则列表
    ('financial/price_rule',PriceruleViewSet),
    # 退款订单
    ('financial/refund_order', RefundOrderViewSet),
    # 对账单
    ('financial/statement', StatementViewset),
    # 开票
    ('financial/ticket', TicketViewset),
    # 报表-对账单查询
    ('financial/tranlist', TranListViewset),
    # 报表-对账单查询
    ('financial/statementexdetail', StatementDetaiExlViewset),
    # execl文件导出
    ('media',MediaExport),
    # 佣金开票
    ('financial/commission_ticket',CommissionTicket),

    ('financial/acctermrule', AccTermRuleViewset),
    ('financial/acctermaction', AccTermActionViewset),
    ('financial/settlement', SettlementViewset),
    ('financial/settlementcommission', SettlementCommissionViewset),

    # 供应商
    ('financial/sup/statement',StatementSupViewset),
    ('financial/sup/statementexdetail', StatementSupDetaiExlViewset),
    ('financial/sup/commission_ticket', CommissionSupTicket),
    ('financial/sup/ticketupload', TicketUploadViewset),
    ('financial/sup/settlement', SettlementSupViewset),
    ('financial/sup/settlementcommission', SettlementCommissionSupViewset),
    ('financial/sup/commission', TicketSupViewset),

]


class RoboRouter(DefaultRouter):
    """
    自定义delete路由
    """
    routes = DefaultRouter.routes
    routes[0] = Route(
        url=r'^{prefix}{trailing_slash}$',
        mapping={
            'get': 'list',
            'post': 'create',
            'put': 'update',
            'delete' : 'destroy',
        },
        name='{basename}-list',
        detail=False,
        initkwargs={'suffix': 'List'}
    )
route=RoboRouter(trailing_slash=False)
for value in iter(route_urls):
    route.register(value[0],value[1],value[0])

urlpatterns=[
        path('v1/', include(route.urls)),
        path('docs/',include_docs_urls(title="财务系统")),
]

