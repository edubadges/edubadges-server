# encoding: utf-8


import json
import os

from django.core.files.storage import DefaultStorage
from django.core.management import BaseCommand

from issuer.models import BadgeClass
from mainsite import TOP_DIR
from mainsite.utils import fetch_remote_file_to_storage


class Command(BaseCommand):
    def handle(self, *args, **options):

        # save the placeholder image to storage if needed
        store = DefaultStorage()
        placeholder_storage_name = "placeholder/badge-failed.svg"
        if not store.exists(placeholder_storage_name):
            with open(os.path.join(TOP_DIR, 'apps', 'mainsite', 'static', 'badgr-ui', 'images', 'badge-failed.svg'), 'r') as fh:
                store.save(placeholder_storage_name, fh)

        report = {
            'total': 0,
            'saved': 0,
            'placeholders_saved': 0,
            'status_codes': {},
            'ioerrors': [],
            'no_image_url': [],
            'json_error': []
        }
        badgeclasses_missing_images = BadgeClass.objects.filter(image='')
        report['total'] = len(badgeclasses_missing_images)
        self.stdout.write("Processing {} badgeclasses missing images...".format(report['total']))
        for badgeclass in badgeclasses_missing_images:
            try:
                original_json = json.loads(badgeclass.original_json)
            except ValueError:
                report['json_error'].append(badgeclass.pk)
            else:
                remote_image_url = original_json.get('image', None)
                if remote_image_url:
                    try:
                        status_code, image = fetch_remote_file_to_storage(remote_image_url, upload_to=badgeclass.image.field.upload_to)
                    except IOError as e:
                        self.stdout.write("IOError fetching '{}': {}".format(remote_image_url, e.message))
                        report['ioerrors'].append((remote_image_url, str(e.message)))
                    else:
                        report['status_codes'][status_code] = report['status_codes'].get(status_code, []) + [remote_image_url]
                        if status_code == 200:
                            badgeclass.image = image
                            badgeclass.save()
                            report['saved'] += 1
                            self.stdout.write("Saved missing image for badgeclass(pk={}) from '{}'".format(badgeclass.pk, remote_image_url))
                            continue  # shortcircuit failure handling at end of loop
                        else:
                            self.stdout.write("Http error fetching '{}': {}".format(remote_image_url, status_code))
                else:
                    report['no_image_url'].append(badgeclass.pk)
                    self.stdout.write("Unable to determine an image url for badgeclass(pk={})".format(badgeclass.pk))

            # all errors should fall through to here
            if not badgeclass.image:
                report['placeholders_saved'] += 1
                badgeclass.image = placeholder_storage_name
                badgeclass.save()
        self.stdout.write(json.dumps(report, indent=2))
