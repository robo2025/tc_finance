from django.db import models
from django.utils import timezone

# Create your models here.
RECEIPT_TYPE = (
    (1, '普通发票'),
    (2, '增值税发票'),
    (3, '无需开票'),
)

PLAN_ORDER_STATUS = (
    (1, '待支付'),
    (2, '已取消'),  # 取消订单
    (3, '备货中'),
    (4, '待发货'),
    (5, '已发货待确认'),
    (6, '客户已确认收货'),
    (7, '订单已完成')
)

PLAN_PAY_STATUS = (
    (1, '首款未支付'),
    (2, '尾款未支付'),
    (3, '已全部支付'),
    (4, '未支付取消'),
    (5, '尾款未支付取消'),
    (6, '支付完成后取消'),
)

PAY_TYPE = (
    (1, '微信支付'),
    (2, '支付宝支付'),
    (3, '银联支付'),
    (4, '其他方式支付')
)

PAYMENT_STATUS = (
    (1, '未支付'),
    (2, '已支付'),
)

CANCEL_TYPE = (
    (1, '未付款取消'),
    (2, '已付款取消')
)

RESPONSIBLE_PARTY = (
    (1, '客户'),
    (2, '供应商'),
    (3, '平台'),
)

OPERATION_STATUS = (
    (1, "提交订单"),
    (2, "支付阶段一"),
    (3, "支付阶段二"),
    (4, "取消订单"),
    (5, "供应商备货"),
    (6, "用户确认收货"),
    (7, "15天自动完成")
)

LOGISTICS_TYPE = (
    (1, '无需物流'),
    (2, '卖家承担运费'),
    (3, '买家承担运费'),
)


class PlanReceipt(models.Model):
    """发票抬头信息"""
    title = models.CharField(max_length=150, verbose_name='发票抬头', null=True, blank=True)
    account = models.CharField(max_length=30, verbose_name='公司账户', null=True, blank=True)
    tax_number = models.CharField(max_length=30, verbose_name='税务编号', null=True, blank=True)
    telephone = models.CharField(max_length=13, verbose_name='公司电话', null=True, blank=True)
    bank = models.CharField(max_length=30, verbose_name='开户行', null=True, blank=True)
    company_address = models.CharField(max_length=200, verbose_name='公司地址', null=True, blank=True, )
    receipt_type = models.IntegerField(choices=RECEIPT_TYPE, default=1, verbose_name='发票类型')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    guest_company_name=None

    class Meta:
        verbose_name = '发票抬头'
        verbose_name_plural = verbose_name
        db_table = 'receipt'
        managed = False

    def __str__(self):
        return self.title


class PlanOrder(models.Model):
    """方案订单"""
    plan_order_sn = models.CharField(max_length=15, verbose_name='方案订单号')
    plan_sn = models.CharField(max_length=20, verbose_name='方案sn号')
    plan_name = models.CharField(max_length=200, verbose_name='方案名', null=True, blank=True)
    industry = models.CharField(max_length=100, verbose_name='行业', null=True, blank=True)
    apply_scene = models.CharField(max_length=200, verbose_name='应用场景', null=True, blank=True)
    sln_type = models.CharField(max_length=50, verbose_name='方案类型', null=True, blank=True)
    receipt_id = models.IntegerField(verbose_name='发票ID', help_text='发票ID')
    status = models.IntegerField(choices=PLAN_ORDER_STATUS, verbose_name='订单状态')
    plan_pay_status = models.IntegerField(choices=PLAN_PAY_STATUS, verbose_name='订单支付状态', default=1)
    receiver = models.CharField(max_length=30, verbose_name='收货人')
    telephone = models.CharField(max_length=11, verbose_name='联系电话')
    mobile = models.CharField(max_length=11, verbose_name='联系电话')
    province = models.CharField(max_length=50, verbose_name='省', blank=True, null=True)
    city = models.CharField(max_length=50, verbose_name='市', blank=True, null=True)
    district = models.CharField(max_length=50, verbose_name='区', blank=True, null=True)
    address = models.CharField(max_length=200, verbose_name='详细地址')
    guest_id = models.IntegerField(verbose_name='客户ID')
    guest_name = models.CharField(max_length=100, verbose_name='客户名', null=True, blank=True)
    guest_company_name = models.CharField(max_length=100, verbose_name='客户公司名', null=True, blank=True)
    supplier_id = models.IntegerField(verbose_name='供应商ID', null=True, blank=True)
    supplier_name = models.CharField(max_length=100, verbose_name='供应商名', null=True, blank=True)
    supplier_company_name = models.CharField(max_length=100, verbose_name='供应商公司名', null=True, blank=True)
    total_money = models.DecimalField(null=True, blank=True, verbose_name='订单总额', help_text='订单总额',
                                      max_digits=18, decimal_places=2)
    number = models.IntegerField(null=True, blank=True, verbose_name='数量')
    remarks = models.TextField(default='', verbose_name='客户备注', help_text='客户备注')
    illustration = models.TextField(default='', verbose_name='方案说明', help_text='方案说明')
    due_time = models.DateTimeField(blank=True, null=True, verbose_name='到期时间', help_text='到期时间')
    delivery_date = models.IntegerField(null=True, blank=True, verbose_name='货期')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '方案订单'
        verbose_name_plural = verbose_name
        db_table = 'plan_order'
        managed = False

    def __str__(self):
        return self.plan_order_sn


class PlanOrderPayment(models.Model):
    """方案订单支付表"""
    plan_order_sn = models.CharField(max_length=15, verbose_name='方案订单号', help_text='方案订单号')
    plan_sn = models.CharField(max_length=20, verbose_name='方案sn号', null=True, blank=True)
    plan_order_pay_sn = models.CharField(max_length=15, verbose_name='方案订单阶段支付号', null=True, blank=True)
    amount = models.DecimalField(verbose_name='应付金额', help_text='应付金额', max_digits=18, decimal_places=2)
    pay_amount = models.DecimalField(verbose_name='实付金额', max_digits=18, decimal_places=2, null=True, blank=True)
    pay_ratio = models.IntegerField(verbose_name='支付比例', null=True, blank=True)
    stage = models.IntegerField(verbose_name='阶段数')
    trade_no = models.CharField(max_length=100, null=True, blank=True, verbose_name='交易流水号')
    pay_type = models.IntegerField(choices=PAY_TYPE, default=1, verbose_name='支付类型')
    pay_status = models.IntegerField(choices=PAYMENT_STATUS, default=1, verbose_name='订单支付状态')
    pay_time = models.DateTimeField(null=True, blank=True, verbose_name='支付时间', help_text='支付时间')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '方案订单支付表'
        verbose_name_plural = verbose_name
        db_table = 'plan_order_payment'
        managed = False

    def __str__(self):
        return self.plan_order_sn


class PlanOrderCancel(models.Model):
    """方案订单取消记录表"""
    plan_order_sn = models.CharField(max_length=15, verbose_name='方案订单号', help_text='方案订单号')
    has_pay_amount = models.DecimalField(verbose_name='已付金额', max_digits=18, decimal_places=2)
    cancel_type = models.IntegerField(choices=CANCEL_TYPE, default=1, verbose_name='取消类型')
    remarks = models.TextField(default='', verbose_name='客户备注', help_text='客户备注')
    responsible_party = models.IntegerField(choices=RESPONSIBLE_PARTY, null=True, blank=True, verbose_name='责任方')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '方案订单取消记录表'
        verbose_name_plural = verbose_name
        db_table = 'plan_order_cancel'
        managed = False

    def __str__(self):
        return self.plan_order_sn


class PlanOrderOperationRecord(models.Model):
    """订单状态操作记录表"""
    plan_order_sn = models.CharField(max_length=15, verbose_name='订单号', help_text='订单号')
    status = models.IntegerField(choices=OPERATION_STATUS, default=1, verbose_name='订单状态', help_text='订单状态')
    operator = models.IntegerField(default=0, verbose_name='操作员', help_text='操作员')
    execution_detail = models.CharField(blank=True, null=True, max_length=100, verbose_name='执行明细', help_text='执行明细')
    progress = models.CharField(blank=True, null=True, max_length=30, verbose_name='当前进度', help_text='当前进度')
    time_consuming = models.FloatField(blank=True, null=True, verbose_name='耗时', help_text='耗时', default=0.0)
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '订单操作'
        verbose_name_plural = verbose_name
        db_table = 'order_operation_record'
        managed = False

    def __str__(self):
        return self.plan_order_sn


class PlanOrderLogistics(models.Model):
    """方案订单物流表"""
    plan_order_sn = models.CharField(max_length=20, verbose_name='订单号', help_text='订单号')
    receiver = models.CharField(max_length=30, verbose_name='收货人', help_text='收货人')
    sender = models.CharField(max_length=30, verbose_name='送货人', help_text='送货人', default='')
    mobile = models.CharField(max_length=11, verbose_name='联系电话', help_text='联系电话')
    address = models.CharField(max_length=400, verbose_name='收货地址', help_text='收货地址')
    logistics_type = models.IntegerField(choices=LOGISTICS_TYPE, default=2, verbose_name='物流方式', help_text='物流方式')
    logistics_company = models.CharField(default='', null=True, blank=True, max_length=100, verbose_name='物流公司',
                                         help_text='物流公司')
    logistics_number = models.CharField(default='', null=True, blank=True, max_length=50, verbose_name='物流编号',
                                        help_text='物流编号')
    add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')

    class Meta:
        verbose_name = '物流单'
        verbose_name_plural = verbose_name
        db_table = 'plan_order_logistics'
        managed = False

    def __str__(self):
        return self.logistics_number
