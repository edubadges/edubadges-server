# encoding: utf-8


from django.conf import settings
from django.test.runner import DiscoverRunner


class BadgrRunner(DiscoverRunner):

    # def __init__(self, *args, **kwargs):
    #     super(BadgrRunner, self).__init__(*args, **kwargs)
    #     self.keepdb = True

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)

        import logging
        import cssutils

        # Silence cssutils completely
        cssutils.log.setLevel(logging.CRITICAL)
        cssutils.log.raiseExceptions = False

        # Also prevent propagation just in case
        logging.getLogger("cssutils").propagate = False

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        if not test_labels and extra_tests is None and 'badgebook' in getattr(settings, 'INSTALLED_APPS', []):
            badgebook_suite = self.build_suite(('badgebook',))
            extra_tests = badgebook_suite._tests
        return super(BadgrRunner, self).run_tests(test_labels, extra_tests=extra_tests, **kwargs)
