import os
# ===============================================================================# 静态资源
# ===============================================================================
# 静态资源文件(js,css等）在APP上线更新后, 由于浏览器有缓存, 可能会造成没更新的情>况.
# 所以在引用静态资源的地方，都把这个加上，如：<script src="/a.js?v=${STATIC_VERSION}"></script>；
# 如果静态资源修改了以后，上线前改这个版本号即可
STATIC_VERSION = 1.0

INSTALLED_APPS_CUSTOM=[
	'rest_framework',
	'django_filters',
	'apps.Finance',
]

# 本地开发环境日志级别
LOG_LEVEL_DEVELOP = 'DEBUG'
# 测试环境日志级别
LOG_LEVEL_TEST = os.environ.get('LOG_LEVEL_TEST', 'INFO')
# 正式环境日志级别
LOG_LEVEL_PRODUCT = os.environ.get('LOG_LEVEL_PRODUCT', 'ERROR')

