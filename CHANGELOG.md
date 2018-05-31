# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).


## [2.8.0]
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
