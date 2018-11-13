# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [2.13.0] - 2018-10-04
 - both /v1/ and /v2/ Assertion PUT endpoints rebake assertion image
 - Automatically notifiy recipient the first time they are awarded an assertion
 - Require a verified email when creating an issuer.


## [2.12.9] - 2018-09-14
 - use png preview images when sharing to social 
 - implement batching for the Rebake all badge images task


## [2.11.5] - 2018-08-14
 - Task to fix issuedOn dates for incorrectly saved backpack assertions
 - Update dependencies on vulnerability alerts: pillow, requests
 - Rebake assertion image when updated with PUT endpoint 
 - Add SSO support for Microsoft Azure
 - Take hardcoded secret keys out of settings.py
 - Implement rate limiting on forgot password


## [2.10.3] - 2018-07-20
  - include an ?expand paramter on /v2/backpack for including badge and issuer information in results
  - GDPR Compliant award notification
  - Add Share to Pinterest 
  - Remove Share to Portfolium 
  - Implement rate limiting on resend verification mail 


## [2.9.0] - 2018-06-18

### New Features
  - Track privacy policy agreements for users. When new versions are published, users should be asked to agree again.
  - Track marketing opt-in for users.
  - Celery task to rebake existing assertions to the defined CURRENT_OBI_VERSION

### Bug Fixes
  - Fixed issue with Android app being unable to login if backpack contains badges with evidence
  - When baking images use the "canonical", unversioned, URL to the assertion as the baked "id" property


## [2.8.0] - 2018-06-05
  - bugfix to ensure /v1/earner/badges endpoint serializer is the same now that OBI_VERSION is 2.0
  - optimize caching of BadgeInstances:
      - existing api clients should behave the same
      - assertion endpoints are now OPTIONALLY paginated with ?num=100 previous and net page will be present on the Link header.
          see https://www.w3.org/Protocols/9707-link-header.html
      - cached_badgeinstances() method has been removed
  - bugfix to ensure that /public endpoints return the original source_url if original created on different service.
  - bugfix to allow re-adding a rejected badge from backpack by re-uploading it
  - allow PUT for BadgeInstances


## [2.7.3] - 2018-04-27
  - bugfix handling returning from SSO login
  - bugfix to correctly send confirmation emails when claiming existing account


## [2.7.1] - 2018-04-17 
  - cleanup to related to opensource release
      - CHANGELOG.md added
      - README updated
  - add support for OpenBadge objects that have 'image' property as an object
  - ability to turn on some ExternalTools for all users
  - switch default OpenBadge version to 2.0 (previously was still 1.1)


## [2.6.10] - 2018-03-20
### Added
