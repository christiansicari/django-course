"""
wait db to be available
"""
from django.core.management.base import BaseCommand
import time
from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to wait for database"""

    def handle(self, **options):
        """entrypoint command """
        self.stdout.write("Waiting for database")
        db_up = False
        count = 0
        while(not db_up):
            try:
                count +=1
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError) as e:
                self.stdout.write(str(count))
                db_up = False
                self.stdout.write("Database unvailable, wait 1 second...")
                time.sleep(1)
        