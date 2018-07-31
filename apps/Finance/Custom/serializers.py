
from decimal import Decimal

from rest_framework import serializers

from ..Custom.db import db

from ..Custom.error import  BusiCustomError
from ..models import (
					PriceRule,
					Statement,
					RefundCheck,
					StatementDetail,
					FinanceReceipt,
					FinanceReceiptList,
					FinanceReceiptListDetail,
					FReceiptListDetail,
					FReceiptList,
					FReceipt)

from ..order_model import (	OrderDetail,OrderPayment,
								Order,Receipt,
							   		OrderCancel,AbnormalOrder,OrderRefund,
							  			OrderOperationRecord)

from ..plan_model import (PlanOrder)

from ..pay_model import Payment,UnionPayRecords,Refund

from .com_method import Get_Supplier,Get_Rule_Code,Get_mse_day,Get_mse_day_msg,datetime_to_timestamp,list_to_query_format,month_sub,string_toDatetime

from utils.exceptions import PubErrorCustom
from utils.cal import time_consuming

from core.http.request import send_request

from FSys.config.extra import PALN_API_TOKEN,PLAN_API_HOST

class PriceRuleSerializer(serializers.ModelSerializer):
	class Meta:
		model=PriceRule
		exclude=('add_time','settle_type','price')

class RefundCheckSerializer(serializers.ModelSerializer):
	cancel_status=serializers.SerializerMethodField()
	son_order_sn=serializers.SerializerMethodField()
	order_date=serializers.SerializerMethodField()
	trade_cancel_date=serializers.SerializerMethodField()
	pay_time=serializers.SerializerMethodField()
	trade_cancel_name=serializers.SerializerMethodField()

	def get_cancel_status(self,obj):
		return 2
	def get_son_order_sn(self,obj):
		return obj.order_code
	def get_order_date(self,obj):
		return datetime_to_timestamp(obj.order_time)
	def get_trade_cancel_date(self,obj):
		return datetime_to_timestamp(obj.trade_cancel_time)
	def get_trade_cancel_name(self,obj):
		return obj.responsible_party
	def get_pay_time(self,obj):
		return datetime_to_timestamp(obj.add_time)

	class Meta:
		model=RefundCheck
		exclude=('add_time','operator','order_time','trade_cancel_time')

class RefundOrderDetailsSerializer:
	def data(refund_sn):

		refund=OrderRefund.objects.using('order').filter(refund_sn=refund_sn)
		if not refund.exists():
			return {}
		refund=refund.first()

		order=OrderDetail.objects.using('order').filter(son_order_sn=refund.order_sn)
		if not order.exists():
			return {}
		order=order.first()

		order_parent = Order.objects.using('order').filter(id=order.order)
		if not order_parent.exists():
			return {}
		order_parent=order_parent.first()


		"""
			goods_order_info：	商品订单信息
			goods_order_list：	商品明细信息
			ticket_info:		开票信息
			custom_info：		客户信息
			supplier_info：		供应商信息
			order_handle_info：	订单操作记录
			refund_info：		退款信息
		"""
		goods_order_info= 	dict()
		goods_order_list= 	dict()
		ticket_info=		dict()
		custom_info=		dict()
		supplier_info=		dict()
		order_handle_info=	list()

		# 商品订单号
		goods_order_info['son_order_sn']=order.son_order_sn
		# 订单号
		goods_order_info['order'] = order_parent.order_sn
		#订单状态
		goods_order_info['status'] = order.status
		#下单时间
		goods_order_info['add_time']=datetime_to_timestamp(order.add_time)
		# 支付状态
		pay=OrderPayment.objects.using('order').filter(order_sn=order.son_order_sn).first()
		goods_order_info['pay_status']=pay.pay_status if pay else ''

		# 商品ID
		goods_order_list['goods_sn'] = order.goods_sn
		# 商品名称
		goods_order_list['goods_name'] = order.goods_name
		# 型号
		goods_order_list['model'] = order.model
		# 单价
		goods_order_list['univalent'] = order.univalent
		# 数量
		goods_order_list['number'] = order.number
		# 发货时间
		goods_order_list['delivery_time'] = datetime_to_timestamp(order.delivery_time) if order.delivery_time else ''
		# 商品小计
		goods_order_list['subtotal_money'] = order.subtotal_money
		# 商品总金额
		goods_order_list['total_amount'] = order.number * order.univalent
		# 实付总金额
		goods_order_list['pay_total_amount'] = goods_order_list['total_amount']

		# 异常说明
		ao = AbnormalOrder.objects.using('order').filter(order_sn=order.son_order_sn).first()
		goods_order_list['supplier_remarks'] = ao.supplier_remarks if ao else ''

		ticket=Receipt.objects.using('order').filter(id=order_parent.receipt)
		if ticket.exists():
			ticket=ticket.first()
			# 公司全称
			ticket_info['title'] = ticket.title
			# 公司账户
			ticket_info['account'] = ticket.account
			# 税务编号
			ticket_info['tax_number'] = ticket.tax_number
			# 公司电话
			ticket_info['telephone'] = ticket.telephone
			# 开户银行
			ticket_info['bank'] = ticket.bank
			# 公司地址
			ticket_info['company_address'] = ticket.company_address

		#联系人
		custom_info['receiver']=order_parent.receiver
		#联系电话
		custom_info['mobile'] = order_parent.mobile
		#收货地址
		custom_info['addr'] = '{0}{1}{2}{3}'.format(order_parent.province,
														order_parent.city,
															order_parent.district,
																order_parent.address)
		#备注
		custom_info['remarks']=order_parent.remarks
		#客户公司名
		custom_info['guest_company_name']=order.guest_company_name


		sup=Get_Supplier(order.supplier_id)
		#联系人
		supplier_info['username']=sup['username']
		#联系电话
		supplier_info['mobile'] = sup['mobile']
		#公司名称
		supplier_info['company'] = sup['profile']['company']
		#收货地址
		supplier_info['district_id'] = sup['profile']['district_id']
		supplier_info['address'] = sup['profile']['address']

		records=OrderOperationRecord.objects.using('order').filter(order_sn=order.son_order_sn).order_by('-add_time')
		if records.exists():
			for record in records:
				order_handle_info.append({
					#操作记录
					'status' : record.status,
					#操作员
					'operator' : record.operator,
					#执行明细
					'execution_detail' : record.execution_detail,
					#当前进度
					'progress' : record.progress,
					#操作时间
					'add_time' : datetime_to_timestamp(record.add_time),
					#耗时
					'time_consuming' : int(record.time_consuming),
				})

		return_data={
			'goods_order_info': goods_order_info,
			'goods_order_list': goods_order_list,
			'ticket_info': ticket_info,
			'custom_info': custom_info,
			'supplier_info': supplier_info,
			'order_handle_info': order_handle_info,
		}

		refundcheck=RefundCheck.objects.filter(refund_sn=refund_sn)
		if refundcheck.exists():
			refundcheck=refundcheck.first()

			return_data['refund_info']={
				# 退款类型
				'refund_type': refund.refund_type,
				# 状态
				'status': refund.status,
				# 客户名称
				'guest_company_name': order.guest_company_name,
				# 订单号
				'order': order.order,
				# 商品订单号
				'son_order_sn': order.son_order_sn,
				# 退款操作日期
				'add_time': datetime_to_timestamp(refund.add_time),
				# 交易金额
				'amount': refund.amount,
				# 应退金额
				'refund_amount': refund.amount,
				# 实退金额
				'retreating_amount': refundcheck.pay_amount,
			}

		return return_data

class CreateStatementSerializer(serializers.Serializer):
    supplier_id=serializers.CharField(default='')
    ym=serializers.CharField(required=True,max_length=7,min_length=7,error_messages={
                                "max_length":"对账期间格式有误！",
                                "min_length": "对账期间格式有误！",
                                "required": "对账期间空！",
    })
    date=serializers.CharField(required=True,max_length=10,min_length=10,error_messages={
                                "max_length":"对账日期格式有误！",
                                "min_length": "对账日期格式有误！",
                                "required": "对账日期空！",
    })
    def validate_supplier_id(self, supplier_id):
        if not supplier_id:
            raise serializers.ValidationError("供应商空！")
        try :
            int(supplier_id)
        except ValueError :
            if supplier_id != 'all':
                raise serializers.ValidationError("供应商格式有误！")

        return 0 if supplier_id=='all' else int(supplier_id)

    # 对账单详情入库
    def insert_statementdetail(self,code=None,statement=None, order_return=None):
        statementdetail = StatementDetail()
        statementdetail.code = code
        statementdetail.order_code = statement['order_code']
        statementdetail.order_status = statement['order_status']
        statementdetail.goods_sn = statement['goods_sn']
        statementdetail.goods_name = statement['goods_name']
        statementdetail.model = statement['model']
        statementdetail.price = statement['price']
        statementdetail.number = statement['number']
        statementdetail.order_date = statement['order_date']
        statementdetail.confirm_date = statement['confirm_date']
        statementdetail.supplier_id = statement['supplier_id']
        statementdetail.supplier_name = statement['supplier_name']
        if order_return:
            statementdetail.other_code = order_return.returns_sn
            statementdetail.refund_amount = statementdetail.price * Decimal(statementdetail.number)
            statementdetail.refund_number = statementdetail.number
            statementdetail.refund_commission = statement['commission']
            statementdetail.refund_date = order_return.add_time.date()
            statementdetail.use_code=order_return.returns_sn
        else:
            statementdetail.pay_total = statementdetail.price * Decimal(statementdetail.number)
            statementdetail.commission = statement['commission']
            statementdetail.use_code=statement['order_code']
        statementdetail.save()
        return statementdetail

    def create(self,validated_data):
        supplier_id=self.validated_data['supplier_id']
        limit=self.validated_data['ym'].replace('-','')
        start_date,end_date=Get_mse_day(int(limit[:4]),int(limit[4:]))
        date=self.validated_data['date']

        last_start_date=str(month_sub(datet=string_toDatetime(start_date),m=1))

        supplier=[]
        if not supplier_id:
            ods=OrderDetail.objects.using('order').filter()
            if ods.exists():
                for od in ods:
                    supplier.append(od.supplier_id)
            ods=PlanOrder.objects.using('plan_order').filter()
            if ods.exists():
                for od in ods:
                    supplier.append(od.supplier_id)
            supplier=list(set(supplier))
        else:
            supplier.append(supplier_id)

        assert len(supplier), "无对账数据"

        #判断供应商在此对账期间是否已对账
        st=Statement.objects.filter(supplier_id__in=supplier,limit=limit)
        if st.exists() :
            for item in st:
                supplier.remove(item.supplier_id)
        assert len(supplier), "请勿重复对账"

        #获取满足条件订单(含普通订单和方案订单)
        statement_list=OrderAllQuery.query_statement(			\
                                status=[7,14],
                                    plan_status=[6,],
                                        start_date=last_start_date,
                                            end_date=end_date,
                                                supplier=tuple(supplier))

        assert len(statement_list), "无对账数据"
        print(statement_list)
        #生成对账单
        insert_statement_dict=dict()
        for statement in statement_list:
            if statement['supplier_id'] not in insert_statement_dict.keys():
                """
                    供应商首次计算账单进入此处
                """
                insert_statement_dict[statement['supplier_id']]={
                    'code' : Get_Rule_Code(type=1),
                    'supplier_id':statement['supplier_id'],
                    'supplier_name':statement['supplier_name'],
                    'limit':limit,
                    'date':date,
                    'goods_total':Decimal(0.0),
                    'commission_total':Decimal(0.0),
                }
            code = insert_statement_dict[statement['supplier_id']]['code']
            if statement['status'] == 7 or statement['status']==6:
                statementdetail = self.insert_statementdetail(code,statement,None)
                insert_statement_dict[statement['supplier_id']]['goods_total'] += \
                                statementdetail.pay_total
                insert_statement_dict[statement['supplier_id']]['commission_total'] += \
                                statementdetail.commission
            else:
                from ..order_model import OrderReturns
                return_obj=OrderReturns.objects.using('order').filter(order_sn=statement['order_code'],status=4)
                if return_obj.exists():
                    obj=return_obj.first()
                    statementdetail = self.insert_statementdetail(code, statement, obj)
                    insert_statement_dict[statement['supplier_id']]['goods_total'] -= statementdetail.refund_amount
                    insert_statement_dict[statement['supplier_id']]['commission_total'] -= statementdetail.refund_commission


        [ Statement.objects.create(**insert_statement_dict[k]) for k in insert_statement_dict ]

        return True

class ModiStatementSerializer(serializers.Serializer):

	status=serializers.IntegerField()

	def update(self, instance, validated_data):

		if validated_data['status']==2 and instance.status==2:
			raise  AssertionError("请勿重复发布！")
		elif validated_data['status']==3 and instance.status==3:
			raise  AssertionError("请勿重复确认！")
		elif validated_data['status']==3 and instance.status==1:
			raise AssertionError("还未发布！")
		elif instance.status==1 and validated_data['status']==2:
			#待发布->已发布
			pass
		elif instance.status==2 and validated_data['status']==3:
			#待确认->已确认
			pass
		else:
			raise AssertionError("状态有误！")

		instance.status=validated_data['status']
		instance.save()
		sts=StatementDetail.objects.filter(code=instance.code)
		if sts.exists():
			for st in sts:
				st.status=validated_data['status']
				st.save()
		return instance

class StatementSerializer(serializers.ModelSerializer):

	cycle=serializers.SerializerMethodField()
	month = serializers.SerializerMethodField()

	def get_cycle(self,obj):
		return "%s-%s"%(Get_mse_day_msg(int(str(obj.limit[:4])),int(str(obj.limit[4:]))))
	def get_month(self,obj):
		return "%s年%s月份"%(str(obj.limit)[:4],str(obj.limit)[4:])

	class Meta:
		model=Statement
		fields = ('supplier_name','month','cycle','code','goods_total',
				  		'commission_total','status','supplier_id','limit')

class StatementDetailSerializer(serializers.ModelSerializer):

	type=serializers.SerializerMethodField()
	order_code = serializers.SerializerMethodField()
	number=serializers.SerializerMethodField()
	amount=serializers.SerializerMethodField()
	commission=serializers.SerializerMethodField()
	date=serializers.SerializerMethodField()

	def get_typename(self,obj):
		return "订单" if not obj.other_code else "退货单"
	def get_number(self,obj):
		return obj.number if not obj.other_code else obj.refund_number
	def get_amount(self,obj):
		return obj.pay_total if not obj.other_code else Decimal(0.0)-obj.refund_amount
	def get_commission(self,obj):
		return obj.commission if not obj.other_code else Decimal(0.0)-obj.refund_commission
	def get_order_code(self,obj):
		return obj.order_code if not obj.other_code else obj.other_code
	def get_date(self,obj):
		return obj.order_date if not obj.other_code else obj.refund_date
	class Meta:
		model=StatementDetail
		fields = ('code','date','confirm_date','typename','order_code',
				  	'goods_name','model','price','number','amount','commission')

class StatementDetailExSerializer(serializers.Serializer):

	limit=serializers.SerializerMethodField()
	term=serializers.SerializerMethodField()
	supplier_id=serializers.CharField()
	supplier_name=serializers.CharField()
	code=serializers.CharField()
	order_date=serializers.CharField()
	type=serializers.SerializerMethodField()
	order_code=serializers.SerializerMethodField()
	goods_name=serializers.CharField()
	model=serializers.CharField()
	price=serializers.SerializerMethodField()
	number=serializers.IntegerField()
	amount=serializers.SerializerMethodField()
	commission=serializers.SerializerMethodField()
	status=serializers.SerializerMethodField()

	def get_limit(self,obj):
		return "{}年{}月".format(str(obj.limit)[:4],str(obj.limit)[4:])

	def get_term(self,obj):
		start_date, end_date = Get_mse_day(int(str(obj.limit)[:4]),int(str(obj.limit)[4:]))
		return '{}年{}月{}日-{}年{}月{}日'.format(
			start_date[:4],start_date[5:7],start_date[8:],
			end_date[:4], end_date[5:7], end_date[8:],
		)
	def get_order_date(self,obj):
		return obj.order_date if obj.use_code[:2]!='TH' else obj.refund_date

	def get_order_code(self,obj):
		return obj.use_code

	def get_price(self,obj):
		return obj.price
	def get_type(self,obj):
		return "订单" if obj.use_code[:2]!='TH' else "退货单"
	def get_number(self,obj):
		return obj.number if obj.use_code[:2]!='TH'  else obj.refund_number
	def get_amount(self,obj):
		return obj.pay_total if obj.use_code[:2]!='TH'  else Decimal(0.0)-obj.refund_amount
	def get_commission(self,obj):
		return obj.commission if obj.use_code[:2]!='TH'  else Decimal(0.0)-obj.refund_commission
	def get_status(self,obj):
		return obj.main_status


class OrderAllQuery:

	@time_consuming
	def query(supplier=None,status=None,plan_status=None,start_date=None,end_date=None):
		#订单
		order_sql= """select \
					s.son_order_sn 				as order_code,		\
					s.status 					as order_status,	\
					s.supplier_id				as supplier_id,		\
					s.supplier_name				as supplier_name,	\
					s.goods_sn					as goods_sn,		\
					s.goods_name				as goods_name,		\
					s.model						as model,			\
					s.univalent					as price,			\
					s.number					as number,			\
					s.commission				as commission,		\
					substr(s.add_time,1,10)		as order_date,		\
					substr(p.add_time,1,10)		as confirm_date,	\
					p.status					as status			\
						\
					from order_detail s    \
					  inner join order_operation_record p  \
						  on  s.son_order_sn = p.order_sn"""
		#方案订单
		plan_order_sql = """select \
							s.plan_order_sn 			as order_code,		\
							s.status 					as order_status,	\
							s.supplier_id				as supplier_id,		\
							s.supplier_name				as supplier_name,	\
							s.plan_sn					as goods_sn,	\
							s.plan_name					as goods_name,		\
							s.sln_type					as model,			\
							s.total_money				as price,			\
							1							as number,			\
							0.0							as commission,		\
							substr(s.add_time,1,10)		as order_date,		\
							substr(p.add_time,1,10)		as confirm_date,	\
							p.status					as status			\
								\
							from plan_order s    \
							  inner join order_operation_record p  \
								  on  s.plan_order_sn = p.plan_order_sn"""

		if supplier:
			order_sql="%s and s.supplier_id in %s"%(order_sql,list_to_query_format(supplier))
			plan_order_sql = "%s and s.supplier_id in %s" % (plan_order_sql, list_to_query_format(supplier))
		if status:
			order_sql="%s and p.status in %s" % (order_sql, list_to_query_format(status))
		if plan_status:
			plan_order_sql = "%s and p.status in %s" % (plan_order_sql, list_to_query_format(plan_status))
		if start_date and end_date:
			order_sql = "%s and p.add_time>='%s' and p.add_time<='%s'" % (order_sql, start_date,end_date)
			plan_order_sql = "%s and p.add_time>='%s' and p.add_time<='%s'" % (plan_order_sql, start_date, end_date)
		order_data=db('order').query_todict(order_sql)
		plan_order_data=db('plan_order').query_todict(plan_order_sql)

		return order_data+plan_order_data

	@time_consuming
	def query_statement(supplier=None, status=None, plan_status=None, start_date=None, end_date=None):
		# 订单
		order_sql = """select \
					s.son_order_sn 				as order_code,		\
					s.status 					as order_status,	\
					s.supplier_id				as supplier_id,		\
					s.supplier_name				as supplier_name,	\
					s.goods_sn					as goods_sn,		\
					s.goods_name				as goods_name,		\
					s.model						as model,			\
					s.univalent					as price,			\
					s.number					as `number`,			\
					s.commission				as commission,		\
					substr(s.add_time,1,10)		as order_date,		\
					substr(p.add_time,1,10)		as confirm_date,	\
					p.status					as status	,		\
					case p.status     \
						when 14 then (select returns_sn from order_returns where order_sn=s.son_order_sn limit 1) \
						else s.son_order_sn end as use_code \
					from order_detail s    \
					  inner join order_operation_record p  \
						  on  s.son_order_sn = p.order_sn"""
		# 方案订单
		plan_order_sql = """select \
							s.plan_order_sn 			as order_code,		\
							s.status 					as order_status,	\
							s.supplier_id				as supplier_id,		\
							s.supplier_name				as supplier_name,	\
							s.plan_sn					as goods_sn,	\
							s.plan_name					as goods_name,		\
							s.sln_type					as model,			\
							s.total_money				as price,			\
							1							as number,			\
							0.0							as commission,		\
							substr(s.add_time,1,10)		as order_date,		\
							substr(p.add_time,1,10)		as confirm_date,	\
							p.status					as status	,		\
							 s.plan_order_sn 			as use_code		\
							from plan_order s    \
							  inner join order_operation_record p  \
								  on  s.plan_order_sn = p.plan_order_sn"""

		if supplier:
			order_sql = "%s and s.supplier_id in %s" % (order_sql, list_to_query_format(supplier))
			plan_order_sql = "%s and s.supplier_id in %s" % (plan_order_sql, list_to_query_format(supplier))
		if status:
			order_sql = "%s and p.status in %s" % (order_sql, list_to_query_format(status))
		if plan_status:
			plan_order_sql = "%s and p.status in %s" % (plan_order_sql, list_to_query_format(plan_status))
		if start_date and end_date:
			order_sql = "%s and p.add_time>='%s' and p.add_time<='%s'" % (order_sql, start_date, end_date)
			plan_order_sql = "%s and p.add_time>='%s' and p.add_time<='%s'" % (plan_order_sql, start_date, end_date)
		order_data = db('order').query_todict(order_sql)
		plan_order_data = db('plan_order').query_todict(plan_order_sql)

		if len(order_data) or len(plan_order_data):
			orders=[]
			for item in order_data:
				orders.append(item['use_code'])
			for item in plan_order_data:
				orders.append(item['use_code'])
			orders_len = len(orders)
			last_limit=start_date[:7].replace('-', '')
			obj=StatementDetail.objects.raw("""
					select t1.*
					from statementdetail as t1
					inner join statement as t2 on t1.code=t2.code
					where t1.use_code in %s and t2.limit=%s
			""",[orders,last_limit])
			for item in obj:
				orders.remove(item.use_code)
			if orders_len > len(orders):
				tmp_order_data=[]
				for obj in  order_data:
					is_Flag=False
					for item in orders:
						if obj['use_code']==item:
							is_Flag=True
							break
					if is_Flag:
						tmp_order_data.append(obj)
				tmp_plan_order_data=[]
				for obj in  plan_order_data:
					is_Flag=False
					for item in orders:
						if obj['use_code']==item:
							is_Flag=True
							break
					if is_Flag:
						tmp_plan_order_data.append(obj)
				order_data=tmp_order_data
				plan_order_data=tmp_plan_order_data

		return order_data + plan_order_data


	def get_supplier(supplier=[]):
		"""
			获取已经下订单的供应商
		"""
		tmp_supplier=[]
		if not supplier:
			objs = OrderDetail.objects.using('order').filter()
			if objs.exists():
				for obj in objs:
					tmp_supplier.append(obj.supplier_id)
			objs = PlanOrder.objects.using('plan_order').filter()
			if not objs.exists():
				return list(set(tmp_supplier))
			else:
				for obj in objs:
					tmp_supplier.append(obj.supplier_id)
			tmp_supplier = list(set(tmp_supplier))
		return tmp_supplier

class PayTranListSerializer(serializers.Serializer):
	guest_company_name=serializers.SerializerMethodField()

	card_type=serializers.SerializerMethodField()
	operation_type=serializers.SerializerMethodField()
	trade_type=serializers.SerializerMethodField()
	pay_amount=serializers.SerializerMethodField()
	unionpayrecords=serializers.SerializerMethodField()

	re_no=serializers.CharField()
	order_no=serializers.CharField()
	transaction_id=serializers.CharField()
	pay_type=serializers.CharField()
	pay_status=serializers.IntegerField()
	txn_time=serializers.IntegerField()
	pay_time=serializers.IntegerField()
	pay_method=serializers.CharField()

	def get_guest_company_name(self,obj):
		return obj.guest_company_name if obj.guest_company_name else ''
	def get_unionpayrecords(self,obj):
		return {"unionpay_card":obj.unionpay_card,"merchant_id":obj.merchant_id}

	def get_card_type(self,obj):
		return '储蓄卡'

	def get_operation_type(self,obj):
		return '货款'

	def get_trade_type(self,obj):
			return '正常购买'

	def get_pay_amount(self,obj):
		return obj.amount

	class Meta:
		model = Payment
		fields = ('operation_type','trade_type','re_no','guest_company_name','order_no',
				  	'card_type','pay_amount','transaction_id','unionpayrecords',
				  		'pay_type','pay_status','txn_time','pay_time','pay_method')

class RefundPayTranListSerializer(serializers.Serializer):

	guest_company_name = serializers.CharField()
	card_type=serializers.SerializerMethodField()
	operation_type=serializers.SerializerMethodField()
	trade_type=serializers.SerializerMethodField()
	pay_amount=serializers.SerializerMethodField()
	unionpayrecords=serializers.SerializerMethodField()
	link_order_sn=serializers.CharField()
	pay_type=serializers.SerializerMethodField()

	re_no=serializers.CharField()
	pay_no=serializers.CharField()
	transaction_id=serializers.CharField()
	refund_status=serializers.CharField()
	txn_time=serializers.IntegerField()
	refund_time=serializers.IntegerField()
	order_no=serializers.CharField()

	def get_unionpayrecords(self,obj):
		return {"unionpay_card":obj.unionpay_card,"merchant_id":obj.merchant_id}

	def get_pay_type(self,obj):
		return 3

	def get_card_type(self,obj):
		return '储蓄卡'

	def get_operation_type(self,obj):
		return '货款'

	def get_trade_type(self,obj):
			return '退款'

	def get_pay_amount(self,obj):
		return obj.amount

class NoFinanceReceiptSerializer(serializers.Serializer):
	guest_company_name=serializers.CharField()
	tax_number=serializers.CharField()
	title=serializers.CharField()
	date=serializers.SerializerMethodField()
	type=serializers.SerializerMethodField()
	order_code=serializers.CharField()
	goods_name=serializers.CharField()
	model=serializers.CharField()
	price=serializers.DecimalField(max_digits=18, decimal_places=2)
	number=serializers.IntegerField()
	amount=serializers.SerializerMethodField()
	ticket_amount=serializers.SerializerMethodField()
	ticket_tot=serializers.SerializerMethodField()
	order_code_tmp=serializers.SerializerMethodField()
	index=serializers.SerializerMethodField()

	def get_date(self,obj):
		return obj.add_time.date()
	def get_type(self,obj):
		return '订单' if obj.order_code[:2]!='TH' else '退货单'

	def get_amount(self,obj):
		return obj.use_pay_total
	def get_ticket_amount(self,obj):
		return obj.use_pay_total
	def get_ticket_tot(self,obj):
		return obj.use_pay_total-obj.ticket_amount
	def get_order_code_tmp(self,obj):
		return obj.order_code
	def get_index(self,obj):
		return obj.order_code

class NoFinanceReceiptPlanOrderSerializer(NoFinanceReceiptSerializer):
	goods_sn=serializers.SerializerMethodField()
	goods_name=serializers.SerializerMethodField()
	model=serializers.SerializerMethodField()
	def get_order_code(self, obj):
		return obj.plan_order_sn
	def get_amount(self,obj):
		return obj.total_money
	def get_ticket_amount(self,obj):
		return obj.total_money
	def get_ticket_tot(self,obj):
		return 0.0
	def get_order_code_tmp(self,obj):
		return obj.plan_order_sn
	def get_index(self,obj):
		return obj.plan_order_sn
	def get_price(self,obj):
		return obj.total_money
	def get_type(self,obj):
		return '订单'
	def get_goods_sn(self,obj):
		return obj.plan_sn
	def get_goods_name(self,obj):
		return obj.plan_name
	def get_model(self,obj):
		return obj.sln_type

class NoFinanceReceiptSerializer1(serializers.Serializer):
	guest_company_name=serializers.CharField()
	receipt_type=serializers.SerializerMethodField()
	add_time=serializers.DateTimeField()
	type=serializers.SerializerMethodField()
	son_order_sn=serializers.SerializerMethodField()
	goods_sn=serializers.CharField()
	goods_name=serializers.CharField()
	model=serializers.CharField()
	title=serializers.CharField()
	company_address=serializers.CharField()
	telephone=serializers.CharField()
	bank=serializers.CharField()
	account=serializers.CharField()
	tax_number=serializers.CharField()
	number=serializers.IntegerField()
	unit=serializers.SerializerMethodField()
	price=serializers.SerializerMethodField()
	amount=serializers.SerializerMethodField()
	ticket_amount=serializers.SerializerMethodField()
	order_operation_record_status=serializers.IntegerField()

	def get_receipt_type(self,obj):
		return obj.receipt_type
	def get_type(self,obj):
		return '订单' if obj.order_operation_record_status==6  else '退货单'
	def get_unit(self,obj):
		return '台'
	def get_price(self,obj):
		return obj.univalent
	def get_amount(self,obj):
		return obj.subtotal_money if obj.order_operation_record_status==6  else Decimal(0.0) - obj.subtotal_money
	def get_ticket_amount(self,obj):
		return obj.subtotal_money if obj.order_operation_record_status==6  else Decimal(0.0)-obj.subtotal_money
	
	def get_son_order_sn(self,obj):
		return obj.son_order_sn if obj.order_operation_record_status==6 else obj.returns_sn

class NoFinanceReceiptPlanOrderDetailSerializer:
	def data(request,obj):
		r_data=[]
		for item in obj:
			flag = send_request(url="%s/v1/sln/%s?role=admin" % ((PLAN_API_HOST),item.plan_sn), token=request.META.get('HTTP_AUTHORIZATION'), method='GET')
			if not flag[0]:
				raise PubErrorCustom("获取方案订单详情错误！")
			if not flag[1] or not len(flag[1]):
				raise PubErrorCustom("无此方案订单数据！")
			for sln_device in flag[1]['supplier']['sln_device']:
				r_data.append({
					"guest_company_name":item.guest_company_name,
					"receipt_type":item.receipt_type,
					"add_time":item.add_time,
					"type":'订单',
					'order_code':item.plan_order_sn,
					'goods_sn':sln_device['device_id'],
					'goods_name':sln_device['device_name'],
					'model':sln_device['device_type'],
					'title':item.title,
					'company_address':item.company_address,
					'telephone':item.telephone,
					'bank':item.bank,
					'account':item.account,
					'tax_number':item.tax_number,
					'son_order_sn':item.plan_order_sn,
					'number':sln_device['device_num'],
					'price':sln_device['device_price'],
					'amount':sln_device['device_num'] * sln_device['device_price'],
					'ticket_amount': sln_device['device_num'] * sln_device['device_price'],
					'order_operation_record_status':item.order_operation_record_status,
					'unit':'台',
					'reset_type':sln_device['device_type'],
				})
			for sln_support in flag[1]['supplier']['sln_support']:
				r_data.append({
					"guest_company_name": item.guest_company_name,
					"receipt_type": item.receipt_type,
					"add_time": item.add_time,
					"type": '订单',
					'order_code': item.plan_order_sn,
					'goods_sn': ''	,
					'goods_name': sln_support['name'],
					'model': '技术支持',
					'title': item.title,
					'company_address': item.company_address,
					'telephone': item.telephone,
					'bank': item.bank,
					'account': item.account,
					'tax_number': item.tax_number,
					'son_order_sn': item.plan_order_sn,
					'number': 1,
					'price': sln_support['price'],
					'amount': 1 * sln_support['price'],
					'ticket_amount': 1 * sln_support['price'],
					'order_operation_record_status': item.order_operation_record_status,
					'unit': '台',
					'reset_type': '技术支持',
				})
		return r_data

class FinanceReceiptSerializer(serializers.ModelSerializer):

	tax_number=serializers.SerializerMethodField()
	ticket_no=serializers.SerializerMethodField()
	receipt_date=serializers.SerializerMethodField()
	date=serializers.SerializerMethodField()
	type=serializers.SerializerMethodField()
	amount=serializers.SerializerMethodField()
	ticket_tot=serializers.SerializerMethodField()
	order_code_tmp=serializers.SerializerMethodField()
	open_receipt_time=serializers.SerializerMethodField()
	receipt_url=serializers.SerializerMethodField()

	title=serializers.SerializerMethodField()
	company_address=serializers.SerializerMethodField()
	telephone=serializers.SerializerMethodField()
	bank=serializers.SerializerMethodField()
	account=serializers.SerializerMethodField()

	def get_title(self,obj):
		return obj.receipt_title
	def get_company_address(self,obj):
		return obj.receipt_addr

	def get_telephone(self,obj):
		return obj.receipt_mobile

	def get_receipt_url(self,obj):
		return obj.img
	def get_bank(self,obj):
		return obj.receipt_bank

	def get_account(self,obj):
		return obj.receipt_account

	def get_tax_number(self,obj):
		return obj.receipt_no
	def get_ticket_no(self,obj):
		return obj.receipt_sn
	def get_receipt_date(self,obj):
		return str(obj.create_time)[:10]
	def get_date(self,obj):
		return str(obj.order_time)[:10]
	def get_type(self,obj):
		return obj.order_type
	def get_amount(self,obj):
		return obj.goods_money
	def get_ticket_tot(self,obj):
		return obj.receipt_money
	def get_order_code_tmp(self,obj):
		return obj.receipt_id
	def get_open_receipt_time(self,obj):
		return datetime_to_timestamp(obj.create_time)

	class Meta:
		model = FinanceReceipt
		fields = '__all__'

class FinanceReceiptDetailSerializer1(serializers.Serializer):

	guest_company_name=serializers.CharField()
	receipt_type=serializers.CharField()
	order_code=serializers.CharField()
	goods_name=serializers.CharField()
	model=serializers.CharField()
	price=serializers.SerializerMethodField()
	number=serializers.IntegerField()
	tax_number=serializers.SerializerMethodField()
	ticket_no=serializers.SerializerMethodField()
	receipt_date=serializers.SerializerMethodField()
	date=serializers.SerializerMethodField()
	type=serializers.SerializerMethodField()
	amount=serializers.SerializerMethodField()
	ticket_tot=serializers.SerializerMethodField()
	order_code_tmp=serializers.SerializerMethodField()
	open_receipt_time=serializers.SerializerMethodField()
	index=serializers.SerializerMethodField()

	def get_price(self,obj):
		return obj.price
	def get_tax_number(self,obj):
		return obj.receipt_no
	def get_ticket_no(self,obj):
		return obj.receipt_sn
	def get_receipt_date(self,obj):
		return str(obj.create_time)[:10]
	def get_date(self,obj):
		return str(obj.order_time)[:10]
	def get_type(self,obj):
		return obj.order_type
	def get_amount(self,obj):
		return obj.goods_money
	def get_ticket_tot(self,obj):
		return obj.receipt_money
	def get_order_code_tmp(self,obj):
		return obj.receipt_sn
	def get_open_receipt_time(self,obj):
		return datetime_to_timestamp(obj.create_time)
	def get_index(self,obj):
		return obj.order_code if obj.order_code[:2]!='FA' else obj.receipt_sn

class FinanceReceiptListSerializer(serializers.ModelSerializer):
	notax=serializers.SerializerMethodField()
	tax_rate=serializers.SerializerMethodField()
	tax=serializers.SerializerMethodField()
	ticket_money=serializers.SerializerMethodField()

	def get_notax(self,obj):
		return obj.taxfree_money
	def get_tax_rate(self,obj):
		return obj.rate
	def get_tax(self,obj):
		return obj.tax_money
	def get_ticket_money(self,obj):
		return obj.total_money

	class Meta:
		model = FinanceReceiptList
		fields = '__all__'

class FinanceReceiptListDetailSerializer(serializers.ModelSerializer):
	amount=serializers.SerializerMethodField()
	ticket_money=serializers.SerializerMethodField()

	def get_amount(self,obj):
		return obj.goods_money

	def get_ticket_money(self,obj):
		return obj.receipt_money


	class Meta:
		model = FinanceReceiptListDetail
		fields = '__all__'

class FinanceReceiptDetailSerializer(serializers.Serializer):
	title=serializers.SerializerMethodField()
	goods_merge=serializers.SerializerMethodField()
	goods_list=serializers.SerializerMethodField()
	receipt_sn=serializers.CharField()

	def get_title(self,obj):
		return FINReceiptSerializer(FReceipt.objects.get(receipt_sn=obj.receipt_sn),many=False).data

	def get_goods_merge(self,obj):
		return FINReceiptListSerializer(FReceiptList.objects.filter(receipt_sn=obj.receipt_sn), many=True).data

	def get_goods_list(self,obj):
		receipt_list_detail=FReceiptListDetail.objects.filter(receipt_sn=obj.receipt_sn)
		if not receipt_list_detail.exists():
			raise PubErrorCustom("数据错误！")
		if receipt_list_detail[0].order_code[:2]=='FA':
			return []
		else:
			return FINReceiptListDetailSerializer(FReceiptListDetail.objects.filter(receipt_sn=obj.receipt_sn), many=True).data

class FReceiptListDetailSerializer(serializers.Serializer):
	receipt_sn = serializers.CharField()
	order_code = serializers.CharField()
	goods_sn = serializers.CharField()
	goods_name = serializers.CharField()
	model = serializers.CharField()
	unit = serializers.CharField()
	number = serializers.IntegerField()
	price = serializers.DecimalField(max_digits=18, decimal_places=2)
	goods_money = serializers.DecimalField(max_digits=18, decimal_places=2)
	commission = serializers.DecimalField(max_digits=18, decimal_places=2)
	receipt_money =serializers.DecimalField(max_digits=18, decimal_places=2)
	
class FReceiptListSerializer(serializers.Serializer):
	receipt_sn = serializers.CharField()
	unit = serializers.CharField()
	number = serializers.IntegerField()
	price = serializers.DecimalField(max_digits=18, decimal_places=2)
	rate = serializers.DecimalField(max_digits=18, decimal_places=2)
	taxfree_money = serializers.DecimalField(max_digits=18, decimal_places=2)
	tax_money=serializers.DecimalField(max_digits=18, decimal_places=2)
	total_money=serializers.DecimalField(max_digits=18, decimal_places=2)
	upd_time=serializers.DateTimeField()
	name=serializers.CharField()

		
class FReceiptSerializer(serializers.Serializer):
	receipt_sn = serializers.CharField()
	receipt_status = serializers.IntegerField()
	guest_company_name = serializers.CharField()
	
	receipt_no = serializers.CharField()
	tax_number = serializers.CharField()
	receipt_type = serializers.IntegerField()
	receipt_title = serializers.CharField()
	receipt_addr = serializers.CharField()
	receipt_mobile = serializers.CharField()
	receipt_bank = serializers.CharField()
	receipt_account = serializers.CharField()
	
	goods_money = serializers.DecimalField(max_digits=18, decimal_places=2)
	receipt_money = serializers.DecimalField(max_digits=18, decimal_places=2)
	
	custom = serializers.CharField()
	addr = serializers.CharField()
	mobile = serializers.CharField()
	img = serializers.CharField()
	receipt_date=serializers.SerializerMethodField()

	def get_receipt_date(self,obj):
		return obj.create_time[:10]

class NoFRceiptSerializer(serializers.Serializer):
	code=serializers.CharField()
	supplier_id=serializers.CharField()
	supplier_name = serializers.CharField()
	limit=serializers.SerializerMethodField()
	date=serializers.SerializerMethodField()
	filter_date=serializers.SerializerMethodField()
	typename=serializers.SerializerMethodField()
	order_code=serializers.SerializerMethodField()
	goods_name=serializers.CharField()
	model=serializers.CharField()
	price=serializers.CharField()
	number=serializers.CharField()
	amount=serializers.SerializerMethodField()
	commission=serializers.SerializerMethodField()
	ticket_amount=serializers.SerializerMethodField()
	tot_amount=serializers.SerializerMethodField()

	def get_limit(self,obj):
		year=str(obj.limit)[:4]
		month=str(obj.limit)[5:]
		return "{}年{}月".format(year,month)
	def get_date(self,obj):
		date=str(obj.order_date if not obj.other_code else obj.refund_date)
		return '{}年{}月{}日'.format(date[:4],date[6:7],date[9:])
	def get_filter_date(self,obj):
		return str(obj.order_date) if not obj.use_code[:2]!='TH' else str(obj.refund_date)
	def get_typename(self,obj):
		return "订单" if not obj.use_code[:2]!='TH' else "退货单"
	def get_amount(self,obj):
		return obj.use_pay_total
	def get_commission(self,obj):
		return obj.use_commission
	def get_ticket_amount(self,obj):
		return obj.use_commission - obj.ticket_amount if not obj.use_code[:2]!='TH' else Decimal(0,0) - abs(obj.use_commission) - abs(obj.ticket_amount)
	def get_tot_amount(self,obj):
		return obj.ticket_amount
	def get_order_code(self,obj):
		return obj.use_code
	
class YesFRceiptSerializer(NoFRceiptSerializer):
	
	def get_tot_amount(self,obj):
		return obj.commission1

class FINReceiptListDetailSerializer(serializers.Serializer):
	goods_name = serializers.CharField()
	model = serializers.CharField()
	number = serializers.IntegerField()
	price = serializers.DecimalField(max_digits=18, decimal_places=2)
	amount = serializers.SerializerMethodField()
	ticket_money = serializers.SerializerMethodField()

	def get_amount(self,obj):
		return obj.goods_money
	def get_ticket_money(self,obj):
		return obj.receipt_money

class FINReceiptListSerializer(serializers.Serializer):
	id=serializers.IntegerField()
	goods_name = serializers.SerializerMethodField()
	price=serializers.SerializerMethodField()
	number=serializers.IntegerField()
	unit = serializers.CharField()
	tax_rate = serializers.SerializerMethodField()
	notax = serializers.SerializerMethodField()
	tax = serializers.SerializerMethodField()
	ticket_money = serializers.SerializerMethodField()

	def get_goods_name(self,obj):
		return obj.name
	def get_price(self,obj):
		return obj.price
	def get_tax_rate(self,obj):
		return obj.rate*100
	def get_notax(self,obj):
		return obj.taxfree_money
	def get_tax(self,obj):
		return obj.tax_money
	def get_ticket_money(self,obj):
		return obj.total_money

class FINReceiptSerializer(serializers.Serializer):
	title = serializers.SerializerMethodField()
	company_address = serializers.SerializerMethodField()
	telephone = serializers.SerializerMethodField()
	receipt_type = serializers.CharField()
	receipt_sn = serializers.CharField()
	tax_number = serializers.CharField()
	receipt_no = serializers.CharField()
	bank = serializers.SerializerMethodField()
	account = serializers.SerializerMethodField()
	open_receipt_time = serializers.SerializerMethodField()
	custom = serializers.CharField()
	addr = serializers.CharField()
	mobile=serializers.CharField()
	receipt_url = serializers.SerializerMethodField()

	def get_title(self,obj):
		return obj.receipt_title
	def get_company_address(self,obj):
		return obj.receipt_addr
	def get_telephone(self,obj):
		return obj.receipt_mobile
	def get_bank(self,obj):
		return obj.receipt_bank
	def get_account(self,obj):
		return obj.receipt_account
	def get_open_receipt_time(self,obj):
		return datetime_to_timestamp(obj.create_time)
	def get_receipt_url(self,obj):
		return obj.img