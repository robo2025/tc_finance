
import os

# ===============================================================================# SSO 配置
# ===============================================================================
SSO_HOST = os.environ.get('SSO_HOST', 'https://testapi.robo2025.com/sso')
SSO_VERIFY = SSO_HOST + '/server/verify'
SSO_EXPIRE_TIME = 24 * 60 * 60

JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'omD4PtIjczXouDCqaiHgh2yhSQMcUwdPZyPXUClJ5ig2H2blaWyW4X0GoMeKxSPf')


# ===============================================================================
# debug toolbar 配置
# ===============================================================================DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': "http://code.jquery.com/jquery-2.1.1.min.js"}

# ID生成器主机地址
ORDER_API_HOST = os.environ.get('ORDER_API_HOST', 'https://testapi.robo2025.com/id-generator')

# 商品信息查询主机
GOODS_API_HOST = os.environ.get('GOODS_API_HOST', 'http://testapi.robo2025.com/shop')

# 扣除库存主机
STOCK_API_HOST = os.environ.get('STOCK_API_HOST', 'http://testapi.robo2025.com/shop')

# 供应商查询主机
SUPPLIER_API_HOST = os.environ.get('SUPPLIER_API_HOST', 'https://testapi.robo2025.com/user')



# CDN域名前缀
CDN_HOST = 'http://imgcdn.robo2025.com/'

# 支付主机
PAYMENT_API_HOST = os.environ.get('PAYMENT_API_HOST', 'https://testapi.robo2025.com/pay')

PAYMENT_API_TOKEN = os.environ.get('PAYMENT_API_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MzE5MDUzODAsInNpZCI6IklRTlVQSFZFREVBWkFBWURQSk5HSDRQWE5CT0FPUTZVT1ZIS1ZQRFVFRkFKWTJHTENVVFEiLCJ1aWQiOjF9.dzsEcMQvvZFRTYDsqQWqeFN_bvuINcJNmUd3muUif9M')

# 方案详情
PLAN_API_HOST= os.environ.get('PLAN_API_HOST', 'https://testapi.robo2025.com/slncenter')
PALN_API_TOKEN=os.environ.get('PAYMENT_API_TOKEN', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1MzE3OTg1ODMsInNpZCI6IklRTlVQSFZFREVBWkFBWURQSk5HSDRQWE5CT0FPUTZVT1ZIS1ZQRFVFRkFKWTJHTENVVFEiLCJ1aWQiOjF9.Fzj1ZqAPMZi1QYev9HcL-g_APB_zKf2Y7ZeM-557h4U')