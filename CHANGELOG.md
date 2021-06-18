# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [4.1.0] - 2021-06-21
- Added an option to the badgeclass to make Narrative and Evicence mandatory.
- Expose new badgeclass attributes in graphql.
- Always retrieve EPPN and Schac homes.
- Updated dependencies Django and Pillow.

## [4.0.0] - 2021-05-31
- Better error message if there are no terms.
- UID has changed.
- Added safe checks to str method.
- Badgeclass drives allowed institution.
- Added allowed institutions to badgeclass.
- Allow awarding and approval of badges of other institutions.
- Revoked assertions do not account for in edit permission.
- Added award other institutions columns.
- Allowed inistitutions to award badges to.
- Added a new demo environment setting to test and experience the edubadges platform.
- Fix the transparancy of composite images in watermark badgeclass image.


## [3.1.0] - 2021-05-03
- Added multi-language support for images
- Added badgeclass counter in catalog
- Updated Django, Pillow
- Issuer must be part of a faculty
- Added direct_awarding_enabled to institution
- Added direct_award graphene endpoints
- Fixed provisionment email institution admin not sent
- Added fetching EPPN from eduID
- Added endpoints for revoking assertions and direct awards in bulk
- Multi langual Name change is allowed if the name is empty
- Added is_demo field to badgr_app
- Name is not required in evidence
- Fixed issues with special characters in names

## [3.0.0] - 2021-03-15
- Added multilanguage fields for Institution, Issuer Group & Issuer
- Added public endpoints for catalog

## [2.1.3] - 2021-03-01
- Bugfix eduID
- Added usage reporting.

## [2.1.2] - 2021-02-15
- Adds archiving option to Issuer Group
- Adds swagger api documentation
- Adds evidence and narrative to assertion data

## [2.1.1] - 2021-01-18
 - Added bilangual email (NL/EN).
 - Adds archiving option to Badgeclass and Issuer

## [2.1.0] - 2020-12-28
 - Added endpoints for public institution page.
 - Added English and Dutch language options for description fields.
 - Added option to indicate if an institution supports formal, non-formal or both badgeclasses.
 - Extended logging.
 - Better handling of duplicate issuer names.
 - Added institution name to endpoints.
 - Updated cryptography from 2.3 to 3.2.
 - Several bug fixes.
