import datetime
from flask import Blueprint, make_response, request
from flask_babel import gettext
from catalogue_app import auth
from catalogue_app.course_routes import utils
from catalogue_app.download_routes.queries import download_queries

# Instantiate blueprint
downloads = Blueprint('downloads', __name__)


@downloads.route('/download-general')
@auth.login_required
def download_general():
	query_func = download_queries.general_tab
	filename = gettext('General Tab')
	response = _create_response(request, query_func, filename)
	return response


# Dashboard and Maps tabs built from same table
@downloads.route('/download-dashboard')
@auth.login_required
def download_dashboard():
	query_func = download_queries.dashboard_tab
	filename = gettext('Dashboard Tab')
	response = _create_response(request, query_func, filename)
	return response


@downloads.route('/download-ratings')
@auth.login_required
def download_ratings():
	query_func = download_queries.ratings_tab
	filename = gettext('Ratings Tab')
	response = _create_response(request, query_func, filename)
	return response


@downloads.route('/download-comments')
@auth.login_required
def download_comments():
	query_func = download_queries.comments_tab
	filename = gettext('Comments Tab')
	response = _create_response(request, query_func, filename)
	return response


def _create_response(request, query_func, filename):
	"""Validate args and create file."""
	# Validate user input
	course_code = utils.validate_course_code(request.args)
	# Run query and build file
	raw_data = _run_query(query_func, course_code)
	response = _create_file(raw_data, filename)
	return response


def _run_query(query_func, course_code):
	"""If course code successfully validated, query its raw
	data, else return error message.
	"""
	if course_code:
		raw_data = query_func(course_code)
	else:
		raw_data = gettext('Course Not Found')
	return raw_data


def _create_file(raw_data, filename):
	"""Create file for download by browser."""
	output = make_response(raw_data)
	timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	# 'attachment' to ensure downloads rather than opened in browser
	output.headers['Content-Disposition'] = 'attachment; filename="{0} {1}.csv"'.format(filename, timestamp)
	output.headers['Content-Type'] = 'text/csv; charset=utf-8'
	return output
