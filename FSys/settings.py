
import os
import sys
from datetime import datetime

from .config.db import *
from .config.custom import *
from .config.extra import *

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))
sys.path.insert(0, os.path.join(BASE_DIR, 'lib'))

SECRET_KEY = 'fw!n&@od*$k$v40)j24tqgj9ynket4*q+dm^1=7^ppfumby^-3'

"""
ROBO_DEPLOY_MODE:
    dev     开发模式 
    test.py    测试模式
    pro     生产模式
"""
env_deploy=os.environ.get("ROBO_DEPLOY_MODE","")
if env_deploy.endswith("pro"):
    DATABASES=DBPRO
    DEBUG=False
    LOG_LEVEL = LOG_LEVEL_PRODUCT
    LOG_CLASS = 'logging.handlers.RotatingFileHandler'
elif env_deploy.endswith("test.py"):
    DATABASES=DBTEST
    DEBUG=False
    LOG_CLASS = 'logging.handlers.RotatingFileHandler'
    LOG_LEVEL = LOG_LEVEL_TEST
else:
    DATABASES=DBDEV
    DEBUG=True
    LOG_LEVEL = LOG_LEVEL_DEVELOP
    LOG_CLASS = 'logging.handlers.RotatingFileHandler'

ALLOWED_HOSTS = ['*']

# 跨域配置
CORS_ORIGIN_ALLOW_ALL = True
CORS_EXPOSE_HEADERS = ['X-Content-Range', 'X-Content-Total','number_tot','amount','commission']

APPEND_SLASH=False

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
]
INSTALLED_APPS+=INSTALLED_APPS_CUSTOM

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

ROOT_URLCONF = 'FSys.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'FSys.wsgi.application'


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/
LANGUAGE_CODE = 'zh-hans'  #中文支持，django1.8以后支持；1.8以前是zh-cn
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'

# 日志器的配置
LOGGING_DIR = os.path.join(BASE_DIR, 'logs')

if not os.path.exists(LOGGING_DIR):
    try:
        os.makedirs(LOGGING_DIR)
    except:
        pass

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s [%(asctime)s] %(pathname)s %(lineno)d %(funcName)s %(process)d %(thread)d \n \t %(message)s \n',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s %(message)s \n'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'root': {
            'class': LOG_CLASS,
            'formatter': 'verbose',
            'filename': os.path.join(LOGGING_DIR, '%s.log' % datetime.now().strftime('%Y-%m-%d')),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5
        },
        'component': {
            'class': LOG_CLASS,
            'formatter': 'verbose',
            'filename': os.path.join(LOGGING_DIR, 'component.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5
        },
        'wb_mysql': {
            'class': LOG_CLASS,
            'formatter': 'verbose',
            'filename': os.path.join(LOGGING_DIR, 'wb_mysql.log'),
            'maxBytes': 1024 * 1024 * 4,
            'backupCount': 5
        },
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
        # the root logger ,用于整个project的logger
        'root': {
            'handlers': ['root'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        # 组件调用日志
        'component': {
            'handlers': ['component'],
            'level': 'WARN',
            'propagate': True,
        },
        # other loggers...
        'django.db.backends': {
            'handlers': ['wb_mysql'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


