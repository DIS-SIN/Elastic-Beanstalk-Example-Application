import pandas as pd
from flask_babel import gettext
from catalogue_app.db import query_mysql
from catalogue_app.course_routes.utils import as_float, as_int, as_percent


class OfferingLocations:
	"""Data for the Offerings per Region -> Province -> City chart."""
	def __init__(self, lang, fiscal_year, course_code):
		self.lang = lang
		self.fiscal_year = fiscal_year
		self.course_code = course_code
		self.data = None
		self.regions = None
		self.provinces = None
		self.cities = None
	
	
	def load(self):
		"""Run all queries and process all raw data."""
		self._load_all_locations()
		self._region_drilldown()
		self._province_drilldown()
		self._city_drilldown()
		# Return self to allow method chaining
		return self
	
	
	def _load_all_locations(self):
		"""Query the DB and extract all offering location data for a given
		course code.
		"""
		field_name_1 = 'offering_region_{0}'.format(self.lang)
		field_name_2 = 'offering_province_{0}'.format(self.lang)
		table_name = 'lsr{0}'.format(self.fiscal_year)
		query = """
			SELECT {0}, {1}, offering_city, COUNT(DISTINCT offering_id)
			FROM {2}
			WHERE course_code = %s AND offering_status IN ('Open - Normal', 'Delivered - Normal')
			GROUP BY {0}, {1}, offering_city;
		""".format(field_name_1, field_name_2, table_name)
		results = query_mysql(query, (self.course_code,))
		results = pd.DataFrame(results, columns=['offering_region', 'offering_province', 'offering_city', 'count'])
		self.data = results
	
	
	def _region_drilldown(self):
		"""Calculate number of offerings per region; include regions with 0
		offerings."""
		results = self.data.groupby('offering_region', as_index=False).sum()
		results = dict(results.values.tolist())
		# Explicitly declare list of regions as want to show all, even if count 0
		regions = [
			gettext('Atlantic'),
			gettext('NCR'),
			gettext('Ontario Region'),
			gettext('Pacific'),
			gettext('Prairie'),
			gettext('Québec Region'),
			gettext('Outside Canada')
		]
		results_processed = [{'name': region, 'drilldown': region, 'y': results.get(region, 0)} for region in regions]
		self.regions = results_processed
	
	
	def _province_drilldown(self):
		"""Calculate number of offerings per province; link provinces to regions."""
		# Get list of regions in which the course has offerings
		regions = self.data.loc[:, 'offering_region'].unique()
		# Counts by province
		counts = self.data.groupby(['offering_region', 'offering_province'], as_index=False).sum()
		# Process into form required by Highcharts
		results_processed = {}
		for region in regions:
			province_counts = counts.loc[counts['offering_region'] == region, ['offering_province', 'count']].values.tolist()
			province_counts_processed = self._process_counts(province_counts)
			results_processed[region] = province_counts_processed
		self.provinces = results_processed
	
	
	def _city_drilldown(self):
		"""Calculate number of offerings per city; link cities to provinces."""
		# Get list of provinces in which the course has offerings
		provinces = self.data.loc[:, 'offering_province'].unique()
		# Counts by city
		counts = self.data.groupby(['offering_province', 'offering_city'], as_index=False).sum()
		# Process into form required by Highcharts
		results_processed = {}
		for province in provinces:
			city_counts = counts.loc[counts['offering_province'] == province, ['offering_city', 'count']].values.tolist()
			results_processed[province] = city_counts
		self.cities = results_processed
	
	
	@staticmethod
	def _process_counts(my_list):
		"""Take a nested list of form [['Ottawa', 10], ...] and covert to
		form [{'name': 'Ottawa', 'drilldown': 'Ottawa, 'y': 10}, ...]
		"""
		results_processed = [{'name': list_[0], 'drilldown': list_[0], 'y': list_[1]} for list_ in my_list]
		return results_processed


class OverallNumbers:
	"""Data for a given fiscal year of the Overall Numbers table."""
	def __init__(self, fiscal_year, course_code):
		self.fiscal_year = fiscal_year
		self.course_code = course_code
		self.counts = []
	
	
	def load(self):
		"""Run all queries and process all raw data."""
		self._offering_status_counts()
		self._offering_additional_counts()
		# Return self to allow method chaining
		return self
	
	
	def _offering_status_counts(self):
		"""Query number of offerings by status for a given fiscal year."""
		table_name = 'lsr{0}'.format(self.fiscal_year)
		query = """
			SELECT offering_status, COUNT(DISTINCT offering_id)
			FROM {0}
			WHERE course_code = %s
			GROUP BY offering_status;
		""".format(table_name)
		results = query_mysql(query, (self.course_code,))
		# Ensure all possible statuses returned
		results = dict(results)
		statuses = {
			gettext('Open Offerings'): 'Open - Normal',
			gettext('Delivered Offerings'): 'Delivered - Normal',
			gettext('Cancelled Offerings'): 'Cancelled - Normal'
		}
		results_processed = [(key, results.get(val, 0)) for (key, val) in statuses.items()]
		self.counts.extend(results_processed)
	
	
	def _offering_additional_counts(self):
		"""Additional offering counts used by School analysts."""
		table_name = 'lsr{0}'.format(self.fiscal_year)
		
		query_client_reqs = """
			SELECT COUNT(DISTINCT offering_id)
			FROM {0}
			WHERE course_code = %s AND client != '' AND offering_status IN ('Open - Normal', 'Delivered - Normal');
		""".format(table_name)
		client_reqs = query_mysql(query_client_reqs, (self.course_code,))
		
		query_regs = """
			SELECT COUNT(reg_id)
			FROM {0}
			WHERE course_code = %s AND reg_status = 'Confirmed';
		""".format(table_name)
		regs = query_mysql(query_regs, (self.course_code,))
		
		query_no_shows = """
			SELECT SUM(no_show)
			FROM {0}
			WHERE course_code = %s;
		""".format(table_name)
		no_shows = query_mysql(query_no_shows, (self.course_code,))
		
		results = [(gettext('Client Requests'), as_int(client_reqs)),
				   (gettext('Registrations'), as_int(regs)),
				   (gettext('No-Shows'), as_int(no_shows))]
		self.counts.extend(results)










def offerings_per_lang(fiscal_year, course_code):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT offering_language, COUNT(DISTINCT offering_id)
		FROM {0}
		WHERE course_code = %s AND offering_status IN ('Open - Normal', 'Delivered - Normal')
		GROUP BY offering_language;
	""".format(table_name)
	results = query_mysql(query, (course_code,))
	
	# Force 'English', 'French', and 'Bilingual' to be returned within dict
	results = dict(results)
	if 'English' not in results:
		results['English'] = 0
	if 'French' not in results:
		results['French'] = 0
	if 'Bilingual' not in results:
		results['Bilingual'] = 0
	return results


def offerings_cancelled(fiscal_year, course_code):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT SUM(a.Mars / b.Mars)
		FROM
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE course_code = %s AND offering_status = 'Cancelled - Normal') AS a,
			 
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE course_code = %s) AS b;
	""".format(table_name)
	results = query_mysql(query, (course_code, course_code))
	return as_percent(results)


# Need to separate global into separate function as using LIKE '%' too slow
def offerings_cancelled_global(fiscal_year):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT SUM(a.Mars / b.Mars)
		FROM
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE business_type = 'Instructor-Led' AND offering_status = 'Cancelled - Normal') AS a,
			 
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE business_type = 'Instructor-Led') AS b;
	""".format(table_name)
	results = query_mysql(query)
	return as_percent(results)


def avg_class_size(fiscal_year, course_code):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT AVG(class_size)
		FROM(
			SELECT COUNT(reg_id) AS class_size
			FROM {0}
			WHERE course_code = %s AND reg_status= 'Confirmed'
			GROUP BY offering_id
		) AS sub_table;
	""".format(table_name)
	results = query_mysql(query, (course_code,))
	return as_int(results)


# Need to separate global into separate function as using LIKE '%' too slow
def avg_class_size_global(fiscal_year):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT AVG(class_size)
		FROM(
			SELECT COUNT(reg_id) AS class_size
			FROM {0}
			WHERE reg_status= 'Confirmed' AND business_type = 'Instructor-Led'
			GROUP BY offering_id
		) AS sub_table;
	""".format(table_name)
	results = query_mysql(query)
	return as_int(results)


def avg_no_shows(fiscal_year, course_code):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT SUM(a.Mars / b.Mars)
		FROM
			(SELECT SUM(no_show) AS Mars
			 FROM {0}
			 WHERE course_code = %s) AS a,
			 
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE course_code = %s AND offering_status IN ('Open - Normal', 'Delivered - Normal')) AS b;
	""".format(table_name)
	results = query_mysql(query, (course_code, course_code))
	return as_float(results)


# Need to separate global into separate function as using LIKE '%' too slow
def avg_no_shows_global(fiscal_year):
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT SUM(a.Mars / b.Mars)
		FROM
			(SELECT SUM(no_show) AS Mars
			 FROM {0}
			 WHERE no_show = 1) AS a,
			 
			(SELECT COUNT(DISTINCT offering_id) AS Mars
			 FROM {0}
			 WHERE business_type = 'Instructor-Led' AND offering_status IN ('Open - Normal', 'Delivered - Normal')) AS b;
	""".format(table_name)
	results = query_mysql(query)
	return as_float(results)
