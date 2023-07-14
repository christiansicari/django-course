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
        while (not db_up):
            try:
                self.check(databases=['default'])
                db_up = True
                self.stdout.write(self.style.SUCCESS('Database available!'))
            except (Psycopg2Error, OperationalError):
                self.stdout.write("Database unvailable, wait 1 second...")
                time.sleep(1)
