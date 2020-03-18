from django.core.management.base import BaseCommand
import traceback


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Running setup seeds... ", end = "")
        try:
            __import__("mainsite.seeds.01_setup")
            print("\033[92mdone!\033[0m")
        except:
            print("\033[91mFAILED!\033[0m")
            traceback.print_exc()
