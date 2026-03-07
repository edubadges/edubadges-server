# Pilot seedbank setup

import os

from django.conf import settings
from django.db import connection


def run():
    sql_file_path = os.path.join(os.path.dirname(__file__), 'pilot_setup.sql')
    with open(sql_file_path, 'r') as sql_file:
        sql_commands = sql_file.read()

    with connection.cursor() as cursor:
        cursor.execute(sql_commands)


run()
