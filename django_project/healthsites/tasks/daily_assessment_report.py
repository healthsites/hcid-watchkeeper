# coding=utf-8
"""Docstring for this file."""
__author__ = 'ismailsunni'
__project_name = 'watchkeeper'
__filename = 'daily_pdf_report'
__date__ = '8/3/15'
__copyright__ = 'imajimatika@gmail.com'
__doc__ = ''

import os
import cStringIO as StringIO
from xhtml2pdf import pisa

from datetime import datetime, timedelta
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf.global_settings import MEDIA_ROOT
from django.template.loader import render_to_string

logger = get_task_logger(__name__)

from healthsites.models.assessment import HealthsiteAssessment
from healthsites.models.daily_report import DailyReport

reports_directory = os.path.abspath(os.path.join(
    MEDIA_ROOT,
    os.path.pardir,
    'reports'))


def generate_html_report(start_time, end_time):
    from datetime import datetime
    assessments = HealthsiteAssessment.objects.filter(
        created_date__gt=start_time,
        created_date__lt=end_time).order_by('-created_date')
    date = datetime.strptime("%d %d %d" % (start_time.year, start_time.month, start_time.day), '%Y %m %d')
    reports = []
    for assessment in assessments:
        reports.append(assessment.get_dict())
    report_html = render_to_string(
        'report_file.html',
        {
            'date': date,
            'number': assessments.count(),
            'assessments': reports
        }
    )
    return report_html, assessments.count()


def html_to_pdf(data, filename):
    pdf = pisa.CreatePDF(StringIO.StringIO(data.encode('utf-8')), file(filename, "wb"), encoding='utf-8')
    return not pdf.err


def generate_report(start_time, end_time):
    """Return an rst report for event and movement.

    :param start_time: Starting time.
    :param end_time: End time.

    """
    raw_report, assessment_number = generate_html_report(start_time, end_time)
    filename = start_time.strftime('Assessment_Report_%Y%m%d') + '.pdf'
    file_path = os.path.join(reports_directory, filename)
    if not os.path.exists(reports_directory):
        logger.info('Reports directory not exists')
        os.makedirs(reports_directory)
    else:
        logger.info('Reports directory exists')

    # Put the pdf generation here
    # xhtml2pdf
    success = html_to_pdf(raw_report, file_path)
    if success:
        logger.info(
            'Success to generate daily report for %s in %s' % (start_time.strftime('%Y %m %d'), file_path))
    else:
        logger.info('Failed to generate daily report for  %s' % start_time.strftime('%Y %m %d'))

    if os.path.exists(file_path):
        try:
            daily_report = DailyReport.objects.get(start_time=start_time, end_time=end_time)
        except DailyReport.DoesNotExist:
            daily_report = DailyReport()
        daily_report.start_time = start_time
        daily_report.end_time = end_time
        daily_report.assessment_number = assessment_number
        daily_report.file_path = file_path
        daily_report.date_time = start_time
        daily_report.save()


@shared_task(name='tasks.daily_assessment_report')
def daily_assessment_report():
    logger.info('Generate daily pdf report on %s' % datetime.now())
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    end_time = datetime.strptime("%d %d %d" % (end_time.year, end_time.month, end_time.day), '%Y %m %d')
    start_time = datetime.strptime("%d %d %d" % (start_time.year, start_time.month, start_time.day), '%Y %m %d')

    generate_report(start_time, end_time)
