import atexit
import logging
from datetime import datetime, timedelta
from django.db import connections
from apscheduler.schedulers.background import BackgroundScheduler


def expired_direct_awards(settings):
    from directaward.models import DirectAward
    from mainsite.utils import EmailMessageMaker
    from mainsite.utils import send_mail

    # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
    connections.close_all()

    half_year_ago = datetime.utcnow() - timedelta(days=6 * 30)
    direct_awards = DirectAward.objects.filter(created_at__lt=half_year_ago, status='Unaccepted').all()
    for direct_award in direct_awards:
        html_message = EmailMessageMaker.create_direct_award_expired_student_mail(direct_award)
        direct_award.delete()
        from lxml.etree import strip_tags
        plain_text = strip_tags(html_message)
        send_mail(subject='You edubadge has expired',
                  message=plain_text, html_message=html_message, recipient_list=[direct_award.recipient_email])


def start_scheduling(settings):
    scheduler = BackgroundScheduler()
    options = {"trigger": "cron", "kwargs": {"settings": settings},
               "misfire_grace_time": 60 * 60 * 12, "coalesce": True}

    scheduler.add_job(func=expired_direct_awards, hour=9, **options)
    scheduler.start()

    logger = logging.getLogger('Badgr.Debug')
    jobs = scheduler.get_jobs()
    for job in jobs:
        logger.info(f"Running {job.name} job at {job.next_run_time}")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())
