
import os

DBHOST=os.environ.get('DBHOST','bj-cdb-nwi3nzcr.sql.tencentcdb.com')
DBPORT=os.environ.get('DBPORT','63668')
DBNAME=os.environ.get('DBNAME','financial')
DBUSER=os.environ.get('DBUSER','robo2025')
DBPASS=os.environ.get('DBPASS','robodev2018')

ORDER_DBNAME=os.environ.get('ORDER_DBNAME','test_robo_order')
PAYMENT_DBNAME=os.environ.get('PAYMENT_DBNAME','test_robo_pay')
PLAN_ORDER_DBNAME=os.environ.get('PLAN_ORDER_DBNAME','test_plan_order')

DBDEV={
	'default':{
		'ENGINE': 'django.db.backends.mysql',
		'NAME': DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		'HOST': DBHOST,
		'PORT': DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB;'},
	},
	'order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'payment': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PAYMENT_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'plan_order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PLAN_ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
}


DBTEST={
	'default':{
		'ENGINE': 'django.db.backends.mysql',
		'NAME': DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		'HOST': DBHOST,
		'PORT': DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB;'},
	},
	'order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'payment': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PAYMENT_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'plan_order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PLAN_ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
}

DBPRO={
	'default':{
		'ENGINE': 'django.db.backends.mysql',
		'NAME': DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		'HOST': DBHOST,
		'PORT': DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB;'},
	},
	'order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'payment': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PAYMENT_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},
	'plan_order': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': PLAN_ORDER_DBNAME,
		'USER': DBUSER,
		'PASSWORD': DBPASS,
		"HOST": DBHOST,
		"PORT": DBPORT,
		'OPTIONS': {'init_command': 'SET default_storage_engine=INNODB'}
	},

}

if __name__=='__main__':
	print(DBDEV,DBTEST,DBPRO)
