# encoding: utf-8
from __future__ import unicode_literals

from django.conf import settings
from django.test.runner import DiscoverRunner


class BadgrRunner(DiscoverRunner):
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels and extra_tests is None and 'badgebook' in getattr(settings, 'INSTALLED_APPS', []):
            badgebook_suite = self.build_suite(('badgebook',))
            extra_tests = badgebook_suite._tests
        return super(BadgrRunner, self).run_tests(test_labels, extra_tests=extra_tests, **kwargs)



