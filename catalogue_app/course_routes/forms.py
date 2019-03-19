import re
from wtforms import Form, SelectField
from catalogue_app.db import query_mysql


def course_form(lang, fiscal_year):
	"""Query list of all course codes and their titles as seen
	in the LSR. Pass to WTForms to make a dropdown menu."""
	field_name = 'course_title_{0}'.format(lang)
	table_name = 'lsr{0}'.format(fiscal_year)
	query = """
		SELECT DISTINCT course_code, {0}
		FROM {1}
		WHERE course_code != 'A230'
		ORDER BY 1 ASC;
	""".format(field_name, table_name)
	results = query_mysql(query)
	
	# SelectField takes list of tuples (pass_value, display_value)
	choices = [(tup[0].upper(), '{0}: {1}'.format(tup[0].upper(), _clean_title(tup[1]))) for tup in results]
	
	class CourseForm(Form):
		# Displaying form_name disabled in 'templates/includes/_formhelpers.html', so pass empty string
		form_name = ''
		course_code = SelectField(form_name, choices=choices)
	
	return CourseForm


# Internal func to remove course codes from titles
regex = re.compile(pattern=r'[(\[]{0,1}[a-zA-Z]{1}\d{3}[)\]]{0,1}')
def _clean_title(course_title):
	"""Remove course codes from titles."""
	return regex.sub('', course_title).strip()
