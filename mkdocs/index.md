# Edubadges Server Documentation

Digital badge management backend for issuing, managing, and sharing Open Badges in educational contexts.

## Overview

- [**Project Overview**](./1.%20Project%20Overview.md) — Technology stack, features, getting started
- [**Architecture Overview**](./2.%20Architecture%20Overview.md) — C4 diagrams, patterns, module breakdown
- [**Workflow Overview**](./3.%20Workflow%20Overview.md) — Core workflows, data flow, state machines

## Deep Dive

Detailed documentation for each major component:

| Component | Description |
|-----------|-------------|
| [**Badge Domain**](./4.%20Deep%20Dive/1.%20Badge%20Domain%20%28issuer%29.md) | Issuer, BadgeClass, BadgeInstance — the core badge domain |
| [**User & Authentication**](./4.%20Deep%20Dive/2.%20User%20Model%20%26%20Authentication.md) | BadgeUser, SSO (eduID/SURFConext), terms, affiliations |
| [**Signing Infrastructure**](./4.%20Deep%20Dive/3.%20Signing%20Infrastructure.md) | Cryptographic keys, assertion timestamping, BTC ledger |
| [**Institutional Hierarchy & RBAC**](./4.%20Deep%20Dive/4.%20Institutional%20Hierarchy%20%26%20RBAC.md) | Institution→Faculty→Issuer, permission cascading |
| [**LTI Integration**](./4.%20Deep%20Dive/5.%20LTI%20Integration.md) | LTI 1.3 OIDC/deep linking, LTI Edu enrollments |
| [**Direct Award System**](./4.%20Deep%20Dive/6.%20Direct%20Award%20System.md) | Bulk badge issuance, scheduled processing, audit trails |
| [**Backpack & Public Verification**](./4.%20Deep%20Dive/7.%20Backpack%20%26%20Public%20Verification.md) | User collections, JSON-LD, Open Badges verification |
| [**Mobile API**](./4.%20Deep%20Dive/8.%20Mobile%20API.md) | Mobile endpoints, token auth, push notifications |
| [**OB3 & BadgeConnect**](./4.%20Deep%20Dive/9.%20Open%20Badges%203%20%26%20BadgeConnect.md) | W3C Verifiable Credentials, agent proxies |
| [**Infrastructure**](./4.%20Deep%20Dive/10.%20Infrastructure%20Components.md) | Caching, logging, notifications, theming, monitoring |

## Quick Links

- [API Documentation (Swagger)](http://localhost:8000/api/schema/swagger-ui/)
- [Staff Admin](http://localhost:8000/staff/)
- [GitHub Repository](https://github.com/edubadges/edubadges-server)
