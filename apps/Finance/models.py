from datetime import datetime

from django.db import models

from apps.Finance.order_model import *
from apps.Finance.pay_model import Payment
from apps.Finance.plan_model import PlanOrder,PlanReceipt


REFUND_CUSTOM_STATUS=(
	(1,'未处理'),
	(2,'已处理'),
)

SETTLE_TYPE=(
	('0','代销'),
	('1','直销'),
)

STATEMENT_STATUS = (
    (1, '待发布'),
    (2, '待确认'),
    (3, '已确认'),
	(4, '供应商确认'),
)

TICKET_STATUS = (
    (1, '未保存'),
    (2, '已保存'),
)
class CustomPlanOrder(PlanOrder):
	receipt_id=None
	order_operation_record_status=None
	type = None

	price=None
	use_pay_total=None
	use_commission=None
	ticket_amount=None
	order_code=None

	tax_number=None
	title=None
	company_address=None
	telephone=None
	bank=None
	account=None
	receipt_type=None

	class Meta:
		managed = False

class CustomOrder(OrderDetail):

	receipt_id=None
	order_sn=None
	returns_sn=None
	order_operation_record_status=None
	link_order_sn=None
	type=None

	price=None
	ticket_amount = None
	use_pay_total=None
	use_commission=None
	order_code=None

	tax_number=None
	title=None
	company_address=None
	telephone=None
	bank=None
	account=None
	receipt_type=None

	class Meta:
		managed = False

class CustomPayment(Payment):
	guest_company_name=None
	unionpay_card=None
	merchant_id=None
	link_order_sn=None

class PriceRule(models.Model):
	id=models.BigAutoField(primary_key=True)
	rulecode=models.CharField(max_length=17,verbose_name='结算单号',default='')
	settle_type=models.CharField(max_length=1,choices=SETTLE_TYPE,verbose_name='结算类型',default='0')
	supplier_id=models.IntegerField(verbose_name='供应商代码')
	supplier_name=models.CharField(max_length=100,verbose_name='供应商名',default='')
	goods_sn=models.CharField(max_length=17,verbose_name='商品号',default='')
	goods_name=models.CharField(max_length=100,verbose_name='商品名',default='')
	goods_model=models.CharField(max_length=100,null=True,verbose_name='商品型号',default='')
	price=models.DecimalField(default=0.0,max_digits=18,decimal_places=2,verbose_name='单价')
	rate=models.DecimalField(default=0.0,max_digits=6,decimal_places=2,verbose_name='佣金比例')
	start_date=models.DateField(null=False,verbose_name='生效日期')
	end_date=models.DateField(null=False,verbose_name='失效日期')
	add_time=models.DateTimeField(default=datetime.now,verbose_name="添加时间")

	class Meta:
		verbose_name='结算价规则表'
		db_table='pricerule'

class RefundCheck(models.Model):
	id=models.BigAutoField(primary_key=True)
	order_code=models.CharField(max_length=60)
	refund_sn = models.CharField(max_length=32)
	supplier_id = models.IntegerField()
	supplier_name = models.CharField(max_length=100)
	guest_id = models.IntegerField()
	guest_company_name = models.CharField(max_length=100)
	order_time = models.DateTimeField()
	trade_cancel_time = models.DateTimeField()
	trade_cancel_remark = models.CharField(max_length=100)
	responsible_party=models.IntegerField(choices=RESPONSIBLE_PARTY)
	trade_amount = models.DecimalField(default=0.0, verbose_name='交易金额', max_digits=18, decimal_places=2, )
	trade_cancel_amount = models.DecimalField(default=0.0,verbose_name='应退金额',max_digits=18,decimal_places=2,)
	pay_amount=models.DecimalField(default=0.0,verbose_name='实退金额',max_digits=18,decimal_places=2,)
	operator = models.IntegerField(verbose_name='操作人',null=True,blank=True)
	add_time = models.DateTimeField(default=timezone.now,verbose_name='添加时间')

	class Meta:
		verbose_name = '退款审核记录'
		db_table = 'refundcheck'

class Statement(models.Model):
	id=models.BigAutoField(primary_key=True)
	code = models.CharField(max_length=17,verbose_name='对账单号')
	supplier_id = models.IntegerField(verbose_name='供应商ID')
	supplier_name = models.CharField(max_length=100,verbose_name='供应商名',null=True,blank=True)
	limit = models.CharField(verbose_name='对账月份',max_length=6,default='')
	goods_total = models.DecimalField(verbose_name='合计金额',max_digits=18,decimal_places=2)
	commission_total = models.DecimalField(verbose_name='佣金合计',max_digits=18,decimal_places=2)
	status = models.IntegerField(choices=STATEMENT_STATUS,verbose_name='状态',default=1)
	date  =  models.DateField(null=True,verbose_name='对账日期')
	confirm_amount = models.DecimalField(verbose_name='确认金额',max_digits=18,decimal_places=2,default=0.0)
	confirm_remark = models.CharField(max_length=1024,verbose_name='备注',default='')
	add_time = models.DateTimeField(default=timezone.now,verbose_name='添加时间')

	class Meta:
		verbose_name = '对账单'
		verbose_name_plural = verbose_name
		db_table = 'statement'

class StatementDetail(models.Model):
	id=models.BigAutoField(primary_key=True)
	code = models.CharField(max_length=17,verbose_name='对账单号')
	order_code = models.CharField(max_length=17,verbose_name='订单号')
	other_code = models.CharField(max_length=32,verbose_name='退款单号',default='')
	order_status = models.IntegerField(choices=ORDER_STATUS,default=0,verbose_name='订单状态')
	supplier_id = models.IntegerField(verbose_name='供应商ID',default=0)
	supplier_name = models.CharField(max_length=100,verbose_name='供应商名',null=True,blank=True)
	goods_sn=models.CharField(max_length=32,verbose_name='商品ID',default='')
	goods_name = models.CharField(max_length=100,verbose_name='商品名',default='')
	model = models.CharField(max_length=100, null=True, verbose_name='型号', default='')
	price = models.DecimalField(default=0.0, verbose_name='单价', max_digits=18, decimal_places=2) #数量
	number = models.IntegerField(default=0, verbose_name='数量')
	commission = models.DecimalField(default=0.0, verbose_name='佣金', max_digits=18, decimal_places=2)
	pay_total = models.DecimalField(default=0.0, verbose_name='实际支付', max_digits=18, decimal_places=2)
	refund_number = models.IntegerField(default=0, verbose_name='退款数量')
	refund_amount = models.DecimalField(default=0.0, verbose_name='退款货款', max_digits=18, decimal_places=2)
	refund_commission = models.DecimalField(default=0.0, verbose_name='退款佣金', max_digits=18, decimal_places=2)
	order_date = models.DateField(null=True, verbose_name='添加时间')
	refund_date = models.DateField(null=True, verbose_name='退款单日期')
	status = models.IntegerField(choices=STATEMENT_STATUS, verbose_name='状态', default=1)
	confirm_date = models.DateField(null=True,verbose_name="确认日期")
	add_time = models.DateTimeField(default=timezone.now, verbose_name='添加时间')
	use_code=models.CharField(max_length=32,verbose_name='订单号/退款单号/方案订单号',default='')
	limit = None
	unit = None
	rest_type = None

	use_pay_total=None
	use_commission=None
	ticket_amount=None

	tax_number=None
	title=None
	company_address=None
	telephone=None
	bank=None
	account=None
	receipt_type=None
	guest_company_name=None
	order_time = None

	receipt_sn = None
	receipt_no = None

	show_number=None

	class Meta:
		verbose_name = '对账单详情'
		verbose_name_plural = verbose_name
		db_table = 'statementdetail'

class FinanceReceipt(models.Model):
	receipt_id = models.BigAutoField(primary_key=True)
	receipt_no = models.CharField(max_length=60,null=True,default='')
	receipt_status = models.IntegerField(choices=TICKET_STATUS,default=1)
	guest_company_name = models.CharField(max_length=255,default='')
	receipt_sn = models.CharField(max_length=60,default='')
	receipt_type = models.IntegerField(choices=RECEIPT_TYPE,default=1)
	receipt_title=models.CharField(max_length=255,default='')
	receipt_addr=models.CharField(max_length=1024,default='')
	receipt_mobile = models.CharField(max_length=20, default='')
	receipt_bank = models.CharField(max_length=20, default='')
	receipt_account = models.CharField(max_length=20, default='')
	order_time = models.DateTimeField(null=True)
	order_type = models.CharField(max_length=30,default='')
	order_code = models.CharField(max_length=60,default='')
	goods_sn = models.CharField(max_length=30,default='')
	goods_name = models.CharField(max_length=255,default='')
	model = models.CharField(max_length=255,default='')
	number = models.IntegerField(default=0)
	price = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
	goods_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
	receipt_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
	custom=models.CharField(max_length=60,null=True,default="")
	addr=models.CharField(max_length=1024,null=True,default="")
	mobile=models.CharField(max_length=20,null=True,default="")
	img=models.CharField(max_length=1024,null=True,default="")
	create_time=models.DateTimeField(default=datetime.now)
	class Meta:
		verbose_name = '开票信息'
		db_table = 'financereceipt'

class FinanceReceiptList(models.Model):

    receipt_listid = models.BigAutoField(primary_key=True)
    receipt_id = models.BigIntegerField()
    receipt_sn = models.CharField(max_length=60, default='')
    goods_sn = models.CharField(max_length=30,default='')
    goods_name = models.CharField(max_length=255,default='')
    model = models.CharField(max_length=255,default='')
    unit = models.CharField(max_length=10,default='')
    number = models.IntegerField(default=0)
    price = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
    rate = models.DecimalField(default=0.16,max_digits=18, decimal_places=2)

    taxfree_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
    tax_money=models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
    total_money=models.DecimalField(default=0.0,max_digits=18, decimal_places=2)

    class Meta:
        verbose_name = '开票信息'
        db_table = 'financereceiptlist'

class FinanceReceiptListDetail(models.Model):
	receipt_listdetailid = models.BigAutoField(primary_key=True)
	receipt_listid=models.BigIntegerField()
	receipt_id = models.BigIntegerField()

	guest_company_name=models.CharField(max_length=100)
	order_time = models.DateTimeField(null=True)
	order_type = models.CharField(max_length=30,default='')
	receipt_sn = models.CharField(max_length=60, default='')
	order_code = models.CharField(max_length=60, default='')
	goods_sn = models.CharField(max_length=30,default='')
	goods_name = models.CharField(max_length=255,default='')
	model = models.CharField(max_length=255,default='')
	unit = models.CharField(max_length=10,default='')
	number = models.IntegerField(default=0)
	price = models.DecimalField(default=0.0,max_digits=18, decimal_places=2)
	goods_money = models.DecimalField(default=0.0, max_digits=18, decimal_places=2)
	receipt_money = models.DecimalField(default=0.0, max_digits=18, decimal_places=2)
	create_time=models.DateTimeField(default=datetime.now,verbose_name="添加时间")
	class Meta:
		verbose_name = '开票信息'
		db_table = 'financereceiptlistdetail'
	receipt_no = None
	receipt_type = None

class FReceipt(models.Model):
	receipt_sn = models.CharField(max_length=60,null=True,default='',verbose_name='发票编号')
	receipt_status = models.IntegerField(choices=TICKET_STATUS,default=1,verbose_name='是否保存开票信息')
	guest_company_name = models.CharField(max_length=255,default='',verbose_name='开票客户')
	
	receipt_no = models.CharField(max_length=60,default='',verbose_name='发票号码')
	tax_number = models.CharField(max_length=60,default='',verbose_name='税务号码')
	receipt_type = models.IntegerField(choices=RECEIPT_TYPE,default=1,verbose_name='发票类型')
	receipt_title=models.CharField(max_length=255,default='',verbose_name='发票抬头')
	receipt_addr=models.CharField(max_length=1024,default='',verbose_name='发票地址')
	receipt_mobile = models.CharField(max_length=20, default='',verbose_name='公司电话')
	receipt_bank = models.CharField(max_length=20, default='',verbose_name='开户行')
	receipt_account = models.CharField(max_length=20, default='开户账号')

	goods_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='货款合计')
	number=models.FloatField(default=0.0,verbose_name='数量合计')
	receipt_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='开票金额')

	custom=models.CharField(max_length=60,null=True,default="",verbose_name='联系人')
	addr=models.CharField(max_length=1024,null=True,default="",verbose_name='联系地址')
	mobile=models.CharField(max_length=20,null=True,default="",verbose_name='联系手机号')
	img=models.CharField(max_length=1024,null=True,default="",verbose_name='发票图片')
	create_time=models.DateTimeField(default=datetime.now,verbose_name='添加时间')
	flag=models.IntegerField(default=1)  #1:货款开票   2:佣金开票

	class Meta:
		verbose_name = '开票信息'
		db_table = 'receipt'

class FReceiptList(models.Model):
	receipt_sn = models.CharField(max_length=60,null=True,default='',verbose_name='发票编号')
	name = models.CharField(max_length=255,default='',verbose_name='货物或应税劳务名称')
	unit = models.CharField(max_length=10,default='',verbose_name='单位')
	number = models.FloatField(default=0.0,verbose_name='数量')
	price = models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='单价')
	rate = models.DecimalField(default=0.16,max_digits=18, decimal_places=2,verbose_name='税率')
	taxfree_money = models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='未税金额')

	tax_money=models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='含税金额')
	total_money=models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='价税合计')
	upd_time=models.DateTimeField(default=datetime.now,verbose_name='修改时间')
	class Meta:
		verbose_name = '开票信息'
		db_table = 'receiptlist'

class FReceiptListDetail(models.Model):
	receipt_sn = models.CharField(max_length=60,null=True,default='',verbose_name='发票编号')
	order_code = models.CharField(max_length=60, default='',verbose_name='订单号/退货号/方案订单号')
	order_time = models.DateTimeField(verbose_name='订单时间')
	goods_sn = models.CharField(max_length=30,default='',verbose_name='商品ID')
	goods_name = models.CharField(max_length=255,default='',verbose_name='商品名称')
	model = models.CharField(max_length=255,default='',verbose_name='型号')
	unit = models.CharField(max_length=10,default='',verbose_name='商品单位')
	number = models.FloatField(default=0.0,verbose_name='商品数量')
	price = models.DecimalField(default=0.0,max_digits=18, decimal_places=2,verbose_name='单价')
	goods_money = models.DecimalField(default=0.0, max_digits=18, decimal_places=2,verbose_name='货款合计')
	commission =  models.DecimalField(default=0.0, max_digits=18, decimal_places=2,verbose_name='佣金')
	receipt_money = models.DecimalField(default=0.0, max_digits=18, decimal_places=2,verbose_name='货款开票金额/佣金开票金额')

	create_time=None
	guest_company_name=None
	total_money=None

	class Meta:
		verbose_name = '开票信息'
		db_table = 'receiptlistdetail'

class AccTermRule(models.Model):
	code=models.CharField(primary_key=True,max_length=60,verbose_name='账期规则代码')
	name=models.CharField(max_length=255,verbose_name='规则名称')
	day=models.IntegerField(default=15)

	class Meta:
		verbose_name = '账期规则表'
		db_table = 'acctermrule'

class AccTermAction(models.Model):
	code=models.CharField(max_length=60,null=True,default='',verbose_name='账期规则代码')
	supplier_id = models.IntegerField(verbose_name='供应商ID')
	supplier_name = models.CharField(max_length=100,verbose_name='供应商名',null=True,blank=True)


	class Meta:
		verbose_name = '账期规则分配表'
		db_table = 'acctermaction'


