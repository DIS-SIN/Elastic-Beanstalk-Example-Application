import json
import mysql.connector
from configparser import ConfigParser

# Get config vals for MySQL
parser = ConfigParser()
parser.read('config.cfg')

def top_5_depts(course_title):
	query = """
			SELECT dept_name, COUNT(dept_name)
			FROM lsr
			WHERE course_title = '{0}' AND reg_status = 'Confirmed' AND no_show = 0
			GROUP BY dept_name
			ORDER BY 2 DESC
			LIMIT 5;
			""".format(course_title)
	
	cnx = mysql.connector.connect(user=parser.get('db', 'user'),
								  password=parser.get('db', 'password'),
								  host=parser.get('db', 'host'),
								  database=parser.get('db', 'database'))
	cursor = cnx.cursor()
	cursor.execute(query)
	results = cursor.fetchall()
	cnx.close()
	return json.dumps(dict(results))