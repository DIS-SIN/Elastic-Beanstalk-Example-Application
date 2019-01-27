import os
from flask import g
import mysql.connector
from catalogue_app.config import Config


def query_mysql(query, args=None, dict_=False):
	"""Execute query on connection stored in g."""
	cnx = get_db(local=Config.LOCAL_DB)
	cursor = cnx.cursor(dictionary=dict_)
	cursor.execute(query, args)
	results = cursor.fetchall()
	cursor.close()
	return results


def get_db(local):
	"""Connect to db and store connection in g for
	life of request.
	"""
	if 'db' not in g:
		if local:
			g.db = mysql.connector.connect(host='localhost',
										   user='admin',
										   password='Newton11',
										   database='csps_dashboards')
		else:
			g.db = mysql.connector.connect(host=os.environ.get('DB_HOST'),
										   user=os.environ.get('DB_USER'),
										   password=os.environ.get('DB_PASSWORD'),
										   database=os.environ.get('DB_DATABASE_NAME'))
	return g.db


def close_db(e=None):
	"""Remove connection to db from g and close."""
	db = g.pop('db', None)
	if db is not None:
		db.close()


def init_app(app):
	"""In factory function, register the close_db function so
	that connections closed at end of request.
	"""
	app.teardown_appcontext(close_db)
