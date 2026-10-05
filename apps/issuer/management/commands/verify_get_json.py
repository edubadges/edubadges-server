from collections import OrderedDict

from django.core.management import BaseCommand
from issuer.models import BadgeClass, BadgeInstance, Issuer


def sorted_dict(d):
    return OrderedDict((k, d[k]) for k in sorted(d.keys()))


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.verbosity = int(options.get("verbosity", 1))
        self.check_jsons(Issuer)
        self.check_jsons(BadgeClass)
        self.check_jsons(BadgeInstance)

    def check_jsons(self, model_cls):
        mismatch = 0
        correct = 0
        for obj in model_cls.objects.all():
            new_json = obj.get_json()
            orig_json = obj.old_json
            if cmp(new_json, orig_json) != 0:  # noqa: F821
                if self.verbosity > 1:
                    self.stdout.write(
                        f"  Jsons don't match! pk={obj.pk}\n  old: {sorted_dict(orig_json)}\n  new: {sorted_dict(new_json)}\n\n"  # noqa: E501
                    )
                mismatch += 1
            else:
                correct += 1

        if self.verbosity > 0:
            self.stdout.write(
                f"Found {mismatch + correct} {model_cls.__name__}s. {correct} correct. {mismatch} mismatch"
            )
