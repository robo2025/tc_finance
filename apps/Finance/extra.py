


from apps.Finance.order_model import OrderDetail,Order



class OrderSysQueryBase(object):


    def __init__(self):
        pass


    def query_order(self,query_sql=str(),where_sql=str(),params=list()):
        """
            根据条件查询订单信息
        """
        pass

    def query_plan_order(self,query_sql=str(),where_sql=str(),params=list()):
        """
            根据条件查询方案订单信息
        """
        pass

    def get_order(self):
        """
            判断是订单号/退货号/方案订单号，并获取
        """