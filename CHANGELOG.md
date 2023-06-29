# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [6.8.1] - 2023-06-29
- Bugfix for new institution.
- Do not display sis integration for new institutions.

## [6.8.0] - 2023-06-05
- Bugfix for teacher security.
- Date reminder.
- Added SIS related fields to DirectAwardBundle.
- Support for client_credentials flow in API.
- Added SIS integration fields to Institution.
- Added redirect URL for swagger OIDC authentication.
- DRF-spectacular extension inline-serializers.
- Added API authorization.
- Hide image API in swagger.
- Formatter.
- Clean up cache for scheduled direct awards.
- Added manage job for awarding scheduled awards.
- Scheduled at is optional.
- Fixed Wrong use of CORS header.
- Added scheduled_at and status to direct award bundle.
- Resend unclaimed direct awards.
- Server side for allowing more then one program identifier.
- Bump cairosvg from 2.5.1 to 2.7.0.
- Bump django from 3.2.17 to 3.2.19.
- Bump cryptography from 3.3.2 to 39.0.1
- Bump sqlparse from 0.2.2 to 0.4.4.
- Bump requests from 2.24.0 to 2.31.0

## [6.7.0] - 2023-02-27
- Issued_on date for assertion is direct_award created_at.
- Revoked assertions are no longer claimed.
- Updated mail templates.
- Delete old / duplicated user provisionings.
- Added linkedin_org_identifier to institution.
- Bump django from 3.2.16 to 3.2.17 .
- Insights type badgeClass.
- Signal the UI for revalidation of the name.
 
## [6.6.0] - 2023-01-16
- Backward incompatibility bugfix for swagger.
- Added help txt to regexp institution.
- After upgrade to django 3.2.16 templates were broken.
- Bump django from 3.2 to 3.2.16.
- Upgrading Pillow 9.2.0.
- Fixed deployment.
- Query for all unclaimed direct awards.
- New command delete_expired_direct_awards.
- Superuser interface backend changes.
- Added logging to scheduled cron job.
- Bugfix for ignoring institution.alternative_identifier in direct award.
- Bugfix for new backpack users.

## [6.5.0] - 2022-10-31
- Exclude expired badge assertions in insights.
- Exclude the free welcome badge in insights.
- Insights: fixed null value due to missing language
- Only select validated assertions in insights.
- Exclude welcome badges in the count of the login screen.
- Update earned_direct_award.html.
- Update base.html.
- Minor changes in the mail templates.
- Explicit version of importlib-metadata.
- Imported concentricsky modules which are no longer available on GitHub.
- Loosened dependency for pytz.
- Bump celery from 4.1.1 to 5.2.2.
- Bump pillow from 8.3.2 to 9.0.1.
- Bump django-celery-results from 1.0.1 to 2.4.0.
- Added revoked before.
- Do not filter on institution if super_user.
- Super users can select institutions in the insights.
- Changed insights queries with group by month.
- WIP on selecting insight based on year and total.
- Bump django-celery-results from 1.0.1 to 2.4.0.

## [6.4.0] - 2022-08-22
- Validation error description.
- Check the Eppn reg exp format.
- Expose eppn_reg_exp_format in Institution.
- Added Direct Award entity in admin view.
- Badgclass option to disable Invite people to enroll.
- changed mailsubject for Direct Awards.

## [6.3.0] - 2022-07-18
- Allow for issuer name changes after assertions have been created.
- Evidence URL is only required when dictated by the badgeclass.
- Refactored cache deletion endorsements.
- Check permissions in delete endorsement.
- Store requested_by in endorsement.
- Resend endorsement mail.
- Sending endorsement email on accept, reject and create.
- Store rejection reason for endorsements.
- Return entityId for public API.
- Check permissions on endorsements.
- Retrieve badge class endorsements in public assertion api.
- Added support for endorsements.
- New endpoint for 3rd parties to validate ownership of badges (OB 2.1). 

## [6.2.0] - 2022-05-16
- Added extra edubadge type filter option in badgeclass overview screen.
- Hide description in related educational framework behind a read more.
- Added more languages of instruction options.
- Related educational framework URL is optional for pilot microcredential badgeclasses.
- Studyload is between 3-30 ECTS for pilot microcredential badgeclasses.
- Bump django from 2.2.26 to 2.2.28 .
- Changed and migrated default languages for institution.
- Ability to disable direct awards for badge classes.
- Send mail if a badge_instance is revoked.
- Serialize is_micro_credentials into database.
- Added option badge class is_micro_credentials.
- Added alternative identifier for institutions.

## [6.1.0] - 2022-03-21
- Small improvement to notifications mail.
- Use the tight URL in notifications.
- Bigfix for wrong url in notifications.
- Added notification template.
- Fetch user notifications through graphene API.
- Storing notification preference per user.
- Allow for student evidence required after assertions.
- Store narrative on the enrollment.
- Added evidence and narrative required for student enrollment on badgeclass.
- Added on behalf fields for faculty.

## [6.0.0] - 2022-02-21
- Changed subject of earned emails and several minor other email tekst.
- Added issuing on behalf of issuer groups.
- Added LTI functionality.
 
## [5.4.0] - 2022-01-17
- Bump Django from 2.2.24 to 2.2.26
- Bump pillow from 8.3.2 to 9.0.0

## [5.3.0] - 2021-12-20
- Minor changes to the information in the mail temlates.
- Added remark to make your edubadges public in the confirmation mail.
- First logout to prevent missing authCode.
- Badgeclass with not revoked assertions is limited updateable.
- Upgraded openbadges.
- Upgrade pypng.
- Added support for signed JWT's in the baked image.
- Do not return archived issuers.

## [5.2.0] - 2021-11-15
- New submodule commits.
- Bugfix for non-unique deny reason enrolllment.
- Check provisionments.
- Added deny_reason to enrollment.
- Proxy call to validator git info.
- Added backpack user count to insights.
- Use connect domain for SURF default.
- Maintain whitelisted url's from Django admin view.
- Imported badges unique for users.
- Fix for multiple whitelisted domains.
- Force build.
- Added public_institution to hide institutions from catalog.

## [5.1.0] - 2021-10-18
- Validate imported badge.
- Added import external open badge functionality.
- New endpoint to delete users by institution admins.
- Do not convert SVG to images for watermark.
- Use the new endpoint in eduID for EPPN's.
- Upgraded graphene django as incompatible with OTP django-object dependency.
- Added 2FA to admin site.
- Allow impersonation by super users.
- Award non-formal edubadge with no validated name.
- Include archived status in catalog.
- If there are validated names, use them.
- Bugfix case-sensitive EPPN rel 5.0.1.
- Added collection functionality to backpack.
- Added evidence information to direct_awards.
- Either Dutch or English attribute is required.
- Added offline exporting JS.
- Bugfix for AnonymousUser does not have is_student.
- Do not fetch accepted enrolments.
- Use database counts for the insights module.
- Updated dependency Pillow.

## [5.0.0] - 2021-08-30
- Added feedback option.
- Overview of all open requested edubadges. 
- Bugfic: multiple emails from same provider are allowed.
- Use cron for scheduling.
- Delete expired direct_awards.
- Clear cache after denied enrollment.
- Migration for formal non-MBO StudyLoad extensions.
- New extension TimeInvestment.
- Show denied enrollments.
- Bugfix for multiple invites.
- Send emails async for direct awards.
- Non-formal badges can be awarded to users with validated name.

## [4.2.0] - 2021-07-19
- Updated dependency Django

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
