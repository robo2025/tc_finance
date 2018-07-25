from enum import Enum

from django.db import models

PAY_STATUS_CHOICE = (
    (0, '未付款'),
    (1, '已付款'),
    (2, '付款撤销'),
    (3, '已退款'),
    (4, '付款超时'),
    (5, '付款错误'),
)

PAY_TYPE_CHOICE = (
    (1, '微信'),
    (2, '支付宝'),
    (3, '银联')
)

TRACE_TYPE_CHOICE = (
    ('pay', '支付'),
    ('refund', '退款'),
    ('undo', '撤销'),
)

PAY_METHOD_CHOICE = (
    ('gateway', '网关'),
    ('b2b', 'b2b'),
)


class TraceType(Enum):
    Pay = 'pay'
    Refund = 'refund'
    Df = 'df'


class PayStatus(Enum):
    NotPaid = 0
    Paid = 1
    Undo = 2
    Refunded = 3


class Payment(models.Model):
    re_no = models.CharField(max_length=50, unique=True)
    order_no = models.CharField(max_length=50)
    user_id = models.IntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_id = models.CharField(max_length=50, null=True)
    pay_type = models.IntegerField(choices=PAY_TYPE_CHOICE)
    pay_method = models.CharField(choices=PAY_METHOD_CHOICE, max_length=20)
    pay_status = models.IntegerField(choices=PAY_STATUS_CHOICE, default=0)
    redirect_url = models.CharField(max_length=200, null=True)
    remark = models.CharField(max_length=1000, null=True)
    created_time = models.BigIntegerField()
    txn_time = models.BigIntegerField('交易发起时间')
    pay_time = models.BigIntegerField(null=True)

    class Meta:
        db_table = 'payment'
        managed = False


class Df(models.Model):
    order_no = models.CharField(max_length=50)
    supplier_id = models.IntegerField()
    payee_name = models.CharField(max_length=50, blank=True, null=True)
    receipt_card_no = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_id = models.CharField(max_length=50, blank=True, null=True)
    pay_type = models.IntegerField(choices=PAY_TYPE_CHOICE)
    pay_status = models.IntegerField(choices=PAY_STATUS_CHOICE, default=0)
    remark = models.CharField(max_length=1000, blank=True, null=True)
    pay_time = models.BigIntegerField(blank=True, null=True)
    created_time = models.BigIntegerField()

    class Meta:
        db_table = 'df'
        managed = False


class UnionPayRecords(models.Model):
    order_no = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=50, unique=True)
    unionpay_card = models.CharField(max_length=30)
    merchant_id = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    trace_type = models.CharField(choices=TRACE_TYPE_CHOICE, max_length=20)
    txn_time = models.BigIntegerField('交易发起时间')
    created_time = models.BigIntegerField()

    class Meta:
        db_table = 'unionpay_records'
        managed = False


REFUND_STATUS_CHOICE = (
    (0, '等待退款'),
    (1, '退款成功'),
    (2, '退款失败'),
)


class RefundStatus(Enum):
    NotRefunded = 0
    Refunded = 1
    Fail = 2


class Refund(models.Model):
    order_no = models.CharField(max_length=30)
    pay_no = models.CharField('付款号', max_length=30)
    re_no = models.CharField('收款号', max_length=30)
    user_id = models.IntegerField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    refund_status = models.IntegerField(choices=REFUND_STATUS_CHOICE, default=0)
    transaction_id = models.CharField(max_length=50, null=True)
    remark = models.CharField(max_length=1000, null=True)
    created_time = models.BigIntegerField()
    txn_time = models.BigIntegerField('交易发起时间')
    refund_time = models.BigIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'refund'
        managed = False


class UnionPayToken(models.Model):
    acc_no = models.CharField(max_length=20)
    token = models.CharField(max_length=50)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'unionpay_token'
        managed = False
