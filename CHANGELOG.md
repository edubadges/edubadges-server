# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [7.4.0] - 2025-02-17

#### Full GitHub changelogs:

Backend: https://github.com/edubadges/edubadges-server/compare/v7.3.1...v7.4.0</br>
Frontend: https://github.com/edubadges/edubadges-ui/compare/V7.3.1...v7.4.0

- Removed panda code and dependency
- Faculty staff no super_user
- Merge pull request #171 from edubadges/feature/fix-duplicate-staff-seed
- feat: Avoid duplicate staff membership errors when seeding
- Merge pull request #170 from edubadges/feature/seed-richer-badges
- Raw users query
- fix: With persisted data, seeds might crash on previously added data
- fix: Don't assume id 1 for badgrapp. When resetting db, it will increment
- fix: Update memcached ENV var, it must be the host:port
- WIP: let seed command fail with errors when it fails
- feat: Add account and badge-instances for student19, demo user
- feat: Add alignment items to several BadgeClasses
- chore: Ensure we don't wipe the database between docker-runs.
- feat: Add a longer, more representative text to criteria in badgeclass
- feat: Add quality assurance to half of the seeded badge-classes
- feat: Add some supervision attributes to the seeds
- feat: Add markdown to badgeclass' description
- New faculties query
- WIP for Issuers query
- Merge branch 'develop' into feature/api-errors-vDlEehUb
- Reverted deletion of super user permission
- Fixed typo for direct_award_audit_trail direct_award_audit_trail() missing 1 required positional argument: 'direct_award_id'
- Fixes for key errors
- Reverted test2
- Added un_successful_direct_awards in response
- Merge branch 'develop' into feature/api-errors-vDlEehUb
- Ignore super users
- WIP for https://trello.com/c/vDlEehUb/
- WIP on catalog performance
- WIP on catalog raw query
- Daniel broke things...
- Resolves 1014-uitbreiden-management-query
- Merge pull request #168 from edubadges/feature/unvalidated-backpack-users-QBYKFZVm
- Updated seed data
- WIP on raw queries
- Small changes after PR review
- WIP for more raw queries
- Redirect to validate name client side
- WIP for QBYKFZVm
- WIP for raw queries
- PoC for raw queries instead of graphQL
- Query edubadge account

## [7.3.1] - 2025-01-27

#### Full GitHub changelogs:

Backend: https://github.com/edubadges/edubadges-server/compare/v7.3.0...v7.3.1</br>
Frontend: https://github.com/edubadges/edubadges-ui/compare/V7.3.0...v7.3.1

- Merge pull request #166 from edubadges/feature/sphereon-random-offer-id
- Merge pull request #165 from edubadges/feature/docker-compose-fix
- Feat: Make the offer-id unpredictable for sphereon
- Chore: Ensure memcached is started before running migrations etc.
- Bugfix for Trello: 987

## [7.3.0] - 2024-12-18

#### Full GitHub changelogs:

Backend: https://github.com/edubadges/edubadges-server/compare/v7.2.0...v7.3.0</br>
Frontend: https://github.com/edubadges/edubadges-ui/compare/V7.2.0...v7.3.0

- Added the option to award edubadges to learners using their mailaddress. This mailaddress should match the one used for eduID.
- Added an option to change the contact mailaddress of the institution.
- Changed mimimal SBU hours (for MBO only) to 80, in steps of 80 with a default of 240 SBU.
- Improved the options to issue on behalf of other organisations.
- New options in the issuergroup functionality to better support virtual organisations.
- Remodelled the placement of logo's of institution, issuergroup and issuer.
- Improved application performance by reducing UI-bundle size.
- Fixed bug when claiming edubadges from other organisations.

## [7.2.0] - 2024-11-13

- Bugfix for single value educationProgramIdentifier.
- Merge pull request #158 from edubadges/revert-156-feature/eppn-email-956.
- Updated graphene-django version to 3.2.2.
- Allow for recipient mail Direct Awards.
- DirectAward can also be owned by recipient_email.
- We don't create welcome badges anymore.
- Added sample_direct_award template for email only.
- Formatter rules.
- Bugfix for assumptation that user has always eppn values.
- Issue #964: direct-award-geen-check-onderwijsinstelling.
- Validated name is only requirement for direct award.
- Fetch DirectAwards by email if bundle type = 'email'.
- We dont use email blacklisting.
- WIP Issue #956: uitreiken-op-prive-mailadres-mogelijk-maken
- Fix issue #961: migration-surf-issuergroups-to-type-test.
- Bugifx for None image_url faculty.
- Create radon.yml.
- Merge pull request #154 from berkes/feature/docker-python-bump.
- Merge pull request #153 from edubadges/feature/extra_eppn_directaward.
- feat: Upgrade python from 3.8 to 3.9 in our app Docker image.
- Merge pull request #152 from edubadges/feature/session_exp.
- Update README.md.
- Added EPPN to badge_assertions in GET directaward bundle.
- Create ruff.yml.
- Create audit.yml.
- Update codeql-analysis.yml.
- Create bandit.yml.
- fix: This tiny rascal kept me busy for days: credentialDataSupplierInput, not Credential.
- feat: Document all attributes and enum items for Educredential.
- feat: Add Glossary for OBv3.
- Migrate all institutions to enable virtual_organization_allowed.
- Default virtual_organization_allowed true.
- Added SESSION_COOKIE_AGE and ruff.toml.
- feat: Add shared network to docker-compose to connect w veramo-agent.
- feat: Attempt to add a debug logger.
- Fix: Ensure payload for sphereon backend is correct.
- refactor: Use the generic ObjectDoesNotExist to avoid pyright error.
- feat: Print offer from Veramo in QR code.
- feat: Extract QR image generation into private method.
- feat: Allow importing of seeded badges for Team Edubadges.
- Issue #942: usecase-uitgeven-surf.
- Issue #944: advanced-issuergroup-functionaliteit.
- Issue #940: sector-kunnen-selecteren-in-de-issuergroup-case-aeres.
- fix: Allow migrations to create indexes that are guaranteed to be under 3072.
- feat: Docker compose with required services.
- Fix unclosed quote in example env var file.

## [7.1.0] - 2024-10-10

- Use of settings vars instead of looking up env vars again.
- Added audit trail for changing validated name.
- Fix for informal MicroCredential (#147).
- BOk2vwtM : Used env vars insteaf of social app db table.
- Improper Input Validation (pentest 2024).
- Disable graphql introspection.
- Searching for badge instances leads to 500 error.
- Tonen kwaliteitskader in de catalogus.
- Uitbreiden query awarded edubadges overview.
- Bugfix superuser.
- Save required extensions if not present.
- Merge pull request #142 from edubadges/feature/directaward_audit.
- Bump cryptography from 42.0.4 to 43.0.1.

## [7.0.0] - 2024-08-14

- fix: Add a type:image to the image payload in our credential request.
- WIP for migration studyload to time-investment for non MBO badges.
- Formal badges are regular badges.
- Update requirements.txt.
- WIP for Banner on login screen.
- fix: New SSI-agent offer response is not JSON but plain text.
- fix: Rename forgotton variable.
- fix: use OfferId, instead of subjectId for impierce ssi-agent.
- fix: Make payload for verification request compatible with ssi-agent.
- Changed endpoint in reference with agent.poc9.eduwallet.nl.
- For private badges we don't require studyload / ects.
- Use JS constants for microcredentials in migration.
- As-is first draft of migration of micro-credential.
- Merge branch 'master' into develop.
- TimeInvestmentExtension is optional for Extra Curricular.
- Expose country_code in institution graphql.
- Added InstitutionCountryExtension.
- Added country code for institutions.
- Force login after logout.
- Added new performant query for requested edubadges.
- Re-enabled BadgeExtensionValidator.
- Temporarily disable validator for extenstions.
- WIP on no-cache for versions/info.
- Added new performant query for requested edubadges.
- Refactored tags.
- Quick - but not final - fix for slow Requested Badges query.
- added more metadata to public bagde class.
- Increased participation.
- Store assessment_types in one column instead of many-to-many.
- Updated gitignore.
- Save grade achieved from requestedbadges.
- Added grades to sample DA.
- Grade required flow.
- Allow for updates of new required fields after assertions are awarded.
- Server side badge class validation.
- WIP for refactoring validation.
- Added extra info for public badge endpoint.
- WIP for extended server side error handling.
- Insights new badge class types.
- criteria_url is no more....
- Tag values in badge overview.
- Added migration for institutions is_micro_credentials_enabled.
- WIP for new badge class forms.
- Institution has badge class tags.
- Extra badge class fields.
- Feature toggle micro_credential.
- Expose badge_class_type.
- Added badge_class_type for new forms.
- Narrow search issuers.
- Management query for issuers.
- Bugfix for query awarded badges.
- Added EPPN to admin views.
- Bump django from 3.2.24 to 3.2.25.
- Bump pillow from 10.2.0 to 10.3.0.
- Bump sqlparse from 0.4.4 to 0.5.0.
- Bump urllib3 from 1.26.18 to 1.26.19.
- Bump djangorestframework from 3.14.0 to 3.15.2.

## [6.10.0] - 2024-02-23

- Synced insights query with management query.
- Upgraded to pillow 10.2.0.
- Optimise management query.
- Admins are super-users.
- Assertions overview query.
- Added total direct award.
- Bugfix for 0 claimrate.
- Query for awarded backpacks.
- Upgraded to latest mysqlclient.
- Bump cryptography from 41.0.4 to 42.0.0.
- Bump django from 3.2.20 to 3.2.24.
- Added issuer and image info to the credential endpoint.
- JSON response for QRcode.
- Bump pycryptodome from 3.18.0 to 3.19.1.
- Added OB3 endpoint.
- Added feature flag for ob3 integration.
- Fix for broken badge query in admin view.
- Bump cryptography from 41.0.4 to 41.0.6.
- Micro-credentials badges.
- Assertion query.
- Added raw query for counts user / assertions.
- Added queries for re-use.

## [6.9.0] - 2023-10-23

- Added micro-credentials count query.
- Code warning resolved.
- Updated mail template requested edubadge.
- Clear cache after resending direct awards.
- Formatted code.
- Badgeoverview query.
- Bugfix for awarding denied enrollments.
- Added institution admins query.
- Do not select direct_awards that are revoked or deleted.
- Return assertions in the direct_award_bundle endpoint.
- Customized documentation Swagger.
- Ensure the direct_award_bundle can only be retrieved with the correct permission.
- Endpoint for SIS API to retrieve DA bundle info.
- Include delete unclaimed DA's in external API.
- Differentiate between unclaimed and deleted diract awards.
- Delete at DA.
- Clear cache after deletion of DA.
- Send mail after direct award deleted.
- Added manage command to delete direct_awards with status 'Delete' and 'Delete_at'.
- Align insight numbers and login numbers.
- Differtiate between direct_awarded and self_request assertions.
- Added authentication logging.
- Exclude create Direct Award from CSRF filter.
- Changed the mail messages for awarded badges.
- Fix datetime warnings in scheduling direct awards.
- Do not display sis integration for new institutions.
- Bugfix for new institution.
- Bump urllib3 from 1.26.17 to 1.26.18.
- Bump pillow from 9.3.0 to 10.0.1.
- Bump urllib3 from 1.26.15 to 1.26.17.
- Bump cryptography from 41.0.3 to 41.0.4.
- Bump cryptography from 41.0.0 to 41.0.3.
- After python 3.9.16 update: urllib3==1.26.15
- Bump cryptography from 39.0.1 to 41.0.0.
- Bump django from 3.2.19 to 3.2.20.

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
