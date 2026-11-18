# Remove unused code: endorsements & credential signing

## Context

Analysis of `edubadges-server` (Django) and its sibling UI `edubadges-ui` (Svelte) shows **both** features in scope are unused in practice:

### Credential signing — dead and broken (server)
- Entry point `POST .../award-enrollments/<id>` with `issue_signed: true` → UI **always** sends `issue_signed: false` (`edubadges-ui/src/api/index.js:154`); `signing_password` is a dead field (zero usages).
- `MaySignAssertions` permission (`apps/signing/permissions.py`) always returns 403; the whole `apps/signing/api.py` is unreachable.
- Signing depends on the missing `chp` CLI binary and a removed external truststore (`TIME_STAMPED_OPEN_BADGES_BASE_URL`); no scheduled job runs `update_timestamp_proofs`; no timestamping has ever completed.
- `BadgeInstance.signature` is never written; `PublicKeyIssuer.public_key` is never populated; no tests exist.

### Endorsements — UI code exists but feature is unused (user-confirmed)
- The UI contains a full endorsement UI (5 components, API layer, GraphQL fragments, ~72 locale keys per language, feature flag) wired into teacher badge-class management and the public badge page.
- **The team does not use the feature** (user feedback 2025-07: "We really do not use endorsements even if there are references in the ui"). → Remove the code from the UI as well.
- Server side: `apps/endorsement/` app (1 model, REST API, emails, GraphQL type), `endorsement-badge-classes` query endpoint, public-badge `expand=endorsements`, 2 email templates, `cached_endorsements`/`cached_endorsed` helpers.
- `edubadges-mobile-app` has **zero** endorsement references (verified by grep) — no mobile work.

## Decisions (user-confirmed)

1. **Full removal of credential signing** — app, models, API, migrations.
2. **Keep `may_sign`** — real DB field on all 4 staff models, `required=True` in staff serializers, used by admin fieldsets and `apps/insights/api.py:314`. Inert data once signing is gone.
3. **Generate drop migrations** — `badgeinstance.signature`, `badgeinstance.public_key_issuer`, the 5 signing tables, **and the `endorsement_endorsement` table**.
4. **Full removal of endorsements** — server app + all UI code (per review feedback).

## Approach

**Two repos, ordered deploy (UI first):**

1. **PR 1 — `edubadges-ui`:** remove all endorsement UI + the dead `issue_signed: false` body field. UI stops calling the endpoints; the old server still answers them, so there is zero downtime and no 404s during rollout.
2. **PR 2 — `edubadges-server`:** remove the endorsement app + all endorsement references, remove all signing code, generate drop migrations, remove the env var. Requires `migrate` in production.
3. **PR 3 — follow-up (after `migrate` ran in prod):** delete the now-empty `apps/endorsement/` and `apps/signing/` directories and drop both from `INSTALLED_APPS` (Django ignores migrations of uninstalled apps, so the drop migrations must already be applied first).

Server PR 2 internals (two commits):
- Commit A: code removal + model field removal; `makemigrations` while both apps are still installed (models emptied) → generated `RemoveField`/`RemoveModel` migrations.
- Commit B (optional, after A is deployed): `INSTALLED_APPS` + directory deletion — recommended as separate follow-up PR instead.

Migration-state notes (verified):
- `is_signer` lives only on the **legacy** `issuer_issuerstaff` table (issuer migration 0047, 2019). The model was later recreated in the `staff` app (staff/0003 → new `staff_issuerstaff` table); the current model has no `is_signer` field, so **no RemoveField needed**. The old table (with its `is_signer` column) is orphaned — optional `DROP TABLE` via one-off RunSQL after confirming it exists in the DB.
- `badgeinstance.signature` added in issuer/0049; `public_key_issuer` FK added in issuer/0051, altered in 0054.
- Signing tables (signing/0001–0006): `signing_symmetrickey`, `signing_privatekey`, `signing_publickey`, `signing_assertiontimestamp`, `signing_publickeyissuer`.
- Endorsement table: `endorsement_endorsement` (endorsement/0001–0002).

## Files to modify

### A. `edubadges-ui` — remove endorsement UI (PR 1)

Delete entirely:
- `src/components/teachers/endorsements/Endorsements.svelte`
- `src/components/teachers/endorsements/Endorsed.svelte`
- `src/components/teachers/endorsements/Endorsement.svelte`
- `src/components/teachers/endorsements/EndorsementView.svelte`
- `src/components/teachers/endorsements/RequestEndorsementModal.svelte`
- `src/util/endorsements.js` (only consumer: `BadgeClassDetails.svelte`)

Modify:
- `src/util/config.js` — remove `endorsements: true` from `features`
- `src/api/index.js`
  - L154: drop `"issue_signed": false` from the award POST body (server field disappears too)
  - L315: `getPublicBadgeClass` — drop `&expand=endorsements` from the query string
  - L826–828: remove `fetchRawEndorsementsBadgeClasses()`
  - L924–951: remove the `//Endorsements` block — `createEndorsement`, `acceptEndorsement`, `rejectEndorsement`, `revokeEndorsement`, `deleteEndorsement`, `resendEndorsement`
- `src/api/queries.js` — remove the `endorsements` fragment (L215–~253) and the `endorsed` fragment (L255–~290). This auto-strips them from every query that interpolates them (4 call sites below).
- `src/components/teachers/ManageBadgeclass.svelte`
  - imports (L8 `endorsed/endorsements` from queries, L21–22 components)
  - initial state `endorsements: [], endorsed: []` (L29)
  - `${endorsements}`/`${endorsed}` in the main query (L131–132)
  - `refreshEndorsements`/`refreshEndorsed` functions (L150–176)
  - endorser/endorsee translation lines (L202–203)
  - sidebar entries `endorsements`/`endorsed` (L249–256)
  - routes `<Route path="/endorsements">` + `<Route path="/endorsed">` (L351–357, incl. `{#if config.features.endorsements}`)
- `src/components/shared/PublicBadgeClassPage.svelte`
  - import `EndorsementView` (L25), `${endorsements}` fragment (L167), `{#if config.features.endorsements} <EndorsementView .../>` block (L426–427)
- `src/components/shared/BadgeClassDetails.svelte`
  - imports (L32–33), state `showEndorsementDetails`/`endorsementsAccepted` (L44–45), onMount filter (L74–76), `toggleEndorsement` (L81–84), CSS `section.alignments, section.endorsements` / `section.endorsement` (L215, L225), template block `{#if endorsementsAccepted...}` (L326–335)
- `src/routes/students/EnrollmentDetails.svelte` — import (L12) + `${endorsements}` in query (L70) (data was fetched but never rendered)
- `src/routes/students/BadgeDetails.svelte` — import (L33) + `${endorsements}` in query (L203)
- `src/locale/en.js` — remove: L332–333 (sidebar labels), L792–793 (`models.badgeclass.endorsement[Multiple]`), L1083–1087 (`endorsements` sub-block), L1338–1339 (zero-states), L1539–1541 (modal field labels), L1925 **adjust** `notifications.info` text (drop the "or if someone requests an endorsement for this edubadge" clause — the notification feature itself stays, it's used by LTI enrollments), L1934–1993 (top-level `endorsements` block)
- `src/locale/nl.js` — same keys at: L333–334, L791–792, L1084–1088, L1338–1339, L1546–1549, L1947–2006 (top-level block). (nl `notifications.info` does not mention endorsements — no change there.)

### B. `edubadges-server` — remove endorsement feature (PR 2)

Delete entirely (contents emptied in PR 2, directory deleted in PR 3):
- `apps/endorsement/` — `models.py` (Endorsement + EndorsementStatus), `api.py`, `api_urls.py`, `serializer.py`, `schema.py` (EndorsementType), `admin.py`, `migrations/` (after generating the drop migration), `__init__.py` etc.

Modify:
- `apps/mainsite/settings.py` — remove `"endorsement"` from `INSTALLED_APPS` (L65) → in PR 3
- `apps/mainsite/urls.py` — remove `path("endorsement/", include("endorsement.api_urls"))` + comment (L87–88)
- `apps/mainsite/drf_spectacluar.py` — remove `"/queries/endorsement-badge-classes"` from included prefixes (L31)
- `apps/queries/api.py` — remove `EndorsementBadgeClasses` view (L1135–~1200)
- `apps/queries/api_urls.py` — remove import (L7) + route (L24)
- `apps/issuer/models.py`
  - `BadgeClass.cached_endorsements` (L637–638), `BadgeClass.cached_endorsed` (L641–642)
  - `BadgeInstance.get_json`: the `json["badge"]["endorsements"] = [BadgeClassJson.endorsement_to_json(bc) ...]` block (L1307–1308, under `expand_user`)
- `apps/issuer/schema.py` — remove `from endorsement.schema import EndorsementType` (L7), `endorsements`/`endorsed` fields (L323–324), `resolve_endorsements`/`resolve_endorsed` (L335–339)
- `apps/public/public_api.py` — remove `expand=endorsements` branch (L422–424) + `BadgeClassJson.endorsement_to_json` (L451–486)
- `apps/mainsite/utils.py` — remove `create_endorsement_requested_mail` (L251–261) + `reject_approve_endorsement_mail` (L263–275)
- `apps/mainsite/templates/email/notification_endorsement.html` — delete
- `apps/mainsite/templates/email/accepted_rejected_endorsement.html` — delete

### C. `edubadges-server` — remove credential signing (PR 2)

Delete entirely (contents emptied in PR 2, directory deleted in PR 3):
- `apps/signing/tsob.py`, `timestamping.py`, `utils.py` (`hash_string` — no external users), `api.py`, `api_urls.py`, `permissions.py`, `serializers.py`, `management/` (whole dir: `update_timestamp_proofs`)

Modify:
- `apps/issuer/models.py`
  - L32–33: remove `from signing import tsob`, `from signing.models import AssertionTimeStamp, PublicKey, PublicKeyIssuer`
  - `Issuer.get_url_with_public_key` (~L314–319), `Issuer.create_empty_key_address` (~L320–328), `Issuer.current_signers` (~L348), `Issuer.create_private_key` (~L361–363)
  - `Issuer.get_json` (~L365–502): drop `signed`/`public_key_issuer`/`expand_public_key` params, guard blocks (L375–380), `if not signed/elif signed` id branch (L403–406), trailing `try/except PublicKey.DoesNotExist` verification block (L493–501)
  - `BadgeClass.issue_signed` (~L871–884)
  - `BadgeClass.get_json` (~L886–925): drop `signed`/`public_key_issuer` params + both signed branches
  - `BadgeInstance.public_key_issuer` field (L996), `BadgeInstance.signature` field (L1062)
  - `BadgeInstance.signing_in_progress` (~L1144–1145), `BadgeInstance.submit_for_timestamping` (~L1146–1149)
  - `BadgeInstance.get_json` (~L1238–1310): drop `signed`/`public_key_issuer` params, validation block (L1247–1253), `if signed` id branch (~L1264–1268), `if signed` badge id (L1290), `signed=`/`public_key_issuer=` kwargs in issuer get_json call (L1292–1298)
- `apps/issuer/api.py` — remove `TimestampedBadgeInstanceList` (L97–119) + `AssertionTimeStamp` import (L20)
- `apps/issuer/api_urls.py` — remove `timestamped-assertions` route + import
- `apps/issuer/serializers.py` — remove `issue_signed` field (L484), `signing_password` field (L485), the `issue_signed` branch in `create` (L575–590)
- `apps/public/public_api.py` — remove `PublicKeyIssuer` import (L31), `IssuerPublicKeyJson` (L355–369), `BadgeClassPublicKeyJson` (L503–513), `if self.object.signature` branch in `BadgeInstanceJson.get_json` (L548–549)
- `apps/public/public_api_urls.py` — remove both `pubkey` routes (L36–38, L51–53) + imports (L11, L20)
- `apps/badgeuser/models.py` — remove `AssertionTimeStamp` import (L36) + `get_assertions_ready_for_signing` (L711–713)
- `apps/staff/models.py` — remove `SymmetricKey` import (L10), `IssuerStaff.may_become_signer` (L207–210), `IssuerStaff.is_signer` property (L212–214)
- `apps/mainsite/settings.py` — remove `TIME_STAMPED_OPEN_BADGES_BASE_URL` (L466)
- `apps/mainsite/urls.py` — remove the `signing/` include (~L95–96)
- `apps/mainsite/drf_spectacluar.py` — optional: drop `"pubkey"` from `excluded_keywords` (routes disappear anyway)
- `env_vars.sh` (L29), `env_vars.sh.example` (L38) — remove `TIME_STAMPED_OPEN_BADGES_BASE_URL`
- `.github/workflows/tests.yml` (L73), `docker-compose.yml` (L48) — remove the env var

### D. New migrations (PR 2, generated with `makemigrations` while both apps still installed)

- `apps/issuer/migrations/0122_*` — `RemoveField badgeinstance.signature`, `RemoveField badgeinstance.public_key_issuer` (Django orders these before the table drops; the FK is PROTECT)
- `apps/signing/migrations/0007_*` — `RemoveModel` × 5 (table drops)
- `apps/endorsement/migrations/0003_*` — `RemoveModel endorsement` (drops `endorsement_endorsement`)
- (optional, after DB check in staging/prod) one-off `RunSQL` migration dropping legacy `issuer_issuerstaff` if present

### Explicitly NOT touched (verified live or unrelated)

- `may_sign` permission field everywhere (staff models/serializers/admin, `insights/api.py:314`)
- `notifications` app + `BadgeClassUserNotification` — used by LTI enrollments and the notification settings UI (only the endorsement-specific senders/emails are removed)
- Email-unsubscribe HMAC signatures (`mainsite/models.py:51–74`, `mainsite/views.py:65`, `account_adapter.py:13`) — unrelated "signature"
- LTI JWK public key (`lti13/models.py:25`) — unrelated
- `edubadges-mobile-app` — no endorsement or signing references exist

## Reuse

No new utilities needed; removal only. Conventions to follow:
- Migration numbering per app (`issuer` at 0121, `signing` at 0006, `endorsement` at 0002)
- `drf_spectacluar.py` already filters `pubkey` from the public schema — no extra cleanup beyond the lines listed
- UI: fragments are composed via template interpolation, so deleting the two fragment exports removes them from all four query call sites in one place

## Steps

- [x] 1. **UI PR:** delete the 5 components in `src/components/teachers/endorsements/` + `src/util/endorsements.js`
- [x] 2. **UI PR:** `api/index.js` (6 API fns + `fetchRawEndorsementsBadgeClasses` + `expand=endorsements` + `issue_signed: false`), `api/queries.js` (2 fragments)
- [x] 3. **UI PR:** remove all endorsement wiring in `ManageBadgeclass.svelte`, `PublicBadgeClassPage.svelte`, `BadgeClassDetails.svelte`, `EnrollmentDetails.svelte`, `BadgeDetails.svelte`; remove `features.endorsements` from `config.js`
- [x] 4. **UI PR:** remove locale keys in `en.js`/`nl.js` (adjust `notifications.info` in en only)
- [x] 5. **UI PR:** `npm run build` + manual smoke (see Verification); merge & **deploy UI**
- [ ] 6. **Server PR:** remove endorsement references in `issuer` (models/schema), `public` (public_api), `queries` (api + urls), `mainsite` (utils, urls, drf_spectacluar, templates), empty `apps/endorsement/models.py`
- [ ] 7. **Server PR:** remove signing code in `issuer`, `public`, `badgeuser`, `staff`, `mainsite`, env files, CI workflow, docker-compose; empty `apps/signing/models.py`
- [ ] 8. **Server PR:** `python manage.py makemigrations issuer staff signing endorsement`; review generated `RemoveField`/`RemoveModel` operations and dependency ordering (field removals before table drops; add `run_before` if a cycle appears)
- [ ] 9. **Server PR:** full test suite + schema generation (see Verification); merge & deploy with `migrate`
- [ ] 10. **Follow-up PR (after `migrate` ran in prod):** remove `"endorsement"` and `"signing"` from `INSTALLED_APPS`, delete `apps/endorsement/` and `apps/signing/` directories
- [ ] 11. (Optional, after DB check) RunSQL migration dropping legacy `issuer_issuerstaff` table if present

## Verification

**UI (PR 1):**
- `npm run build` passes (Svelte compiler catches dangling imports)
- Grep sweep in `edubadges-ui/src`: zero hits for `endorse`/`Endorse` (case-insensitive)
- Manual smoke: teacher badge-class management loads without Endorsements/Endorsed tabs; public badge page renders without the endorsements section; student enrollment + badge detail pages work; badge award flow works (body no longer contains `issue_signed`); notification settings text no longer mentions endorsements
- GraphQL check in devtools: badge class queries no longer select `endorsements`/`endorsed`

**Server (PR 2):**
- `python manage.py check` — no import errors after removals
- `python manage.py makemigrations --check --dry-run` — clean after step 8
- `python manage.py migrate` on a local DB — tables `signing_*` and `endorsement_endorsement` dropped, `signature`/`public_key_issuer` columns gone (psql `\d badgeinstance`)
- Run the test suite as in `.github/workflows/tests.yml` (env minus `TIME_STAMPED_OPEN_BADGES_BASE_URL`)
- `python manage.py spectacular --file schema.yml` — no `pubkey`/`signing`/`endorsement` paths; diff vs old schema: only removed paths differ
- Grep sweep in `apps/`: zero hits for `tsob`, `timestamping`, `chp`, `TIME_STAMPED`, `AssertionTimeStamp`, `PublicKeyIssuer`, `submit_for_timestamping`, `signing_password`, `issue_signed`, `signing_in_progress`, `Endorsement` (outside the emptied app dirs); `endorsement`/`signing` remain only in `INSTALLED_APPS` until PR 3
- API contract: POST award-enrollments still 200s without `issue_signed`; `GET /public/badges/<id>?expand=endorsements` still 200s (unknown expand ignored) until server deploy, then simply absent
- Post-deploy: `/endorsement/*`, `/queries/endorsement-badge-classes`, `/issuer/*timestamped*`, `*/pubkey` routes all 404; GraphQL introspection shows no `endorsements`/`endorsed` fields on BadgeClass; public badge JSON has no `endorsements`/`endorsed` keys
- Admin smoke: staff permission edit with `may_sign` still round-trips (field untouched)

## Risks / notes

- **Deploy order matters:** UI must deploy before the server PR — otherwise the old UI 404s on endorsement calls.
- Dropping `endorsement_endorsement` deletes any existing endorsement rows — acceptable, feature confirmed unused.
- Public badge JSON loses `endorsements`/`endorsed` keys — the UI was the only known consumer; mobile app verified to have none.
- Existing endorsement-related emails in flight (none expected) would be affected — ignore.
