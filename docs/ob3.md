# Open Badges 3.0 (OB3) Integration

## Overview

The `ob3` app provides support for issuing Open Badges 3.0 credentials to digital wallets using the OpenID for Verifiable Credential Issuance (OID4VCI) protocol. This allows badge recipients to receive their edubadges as verifiable credentials in their personal digital wallets, making credentials more portable and user-controlled.

## Context: Badgr and Open Badges Evolution

The edubadges-server is built on Badgr, which implements the **Open Badges 2.0** specification. While OB 2.0 has served the community well, the credentials landscape is evolving toward **Open Badges 3.0** and **verifiable credentials**.

The key difference: OB 3.0 credentials are verifiable credentials that can be stored in digital wallets and verified cryptographically, aligning with emerging standards like the European Digital Identity Wallet framework. This is researched in a SURF and NPULS project called EduWallet Incubater, EWI.

The OB3 app extends the existing edubadges infrastructure to support this new standard without requiring a complete platform rewrite.

## How It Works

### High-Level Architecture

The OB3 app acts as a translation layer:

1. Takes an existing badge instance (OB 2.0 format)
2. Transforms it into an OB 3.0 verifiable credential
3. Sends it to a wallet agent service
4. Returns a credential offer to the recipient
5. Recipient claims the credential in their digital wallet

### Why Models and Serializers?

Building complex, nested JSON structures for OB 3.0 credentials with all the necessary business logic proved too unwieldy for template-based approaches. Instead, we chose to:

- **Models**: Plain Python objects that encapsulate the business logic and data structure of credentials
- **Serializers**: Django REST Framework serializers that transform these models into spec-compliant JSON

This separation keeps business logic clean and maintainable while ensuring the output always matches the OB 3.0 specification.

### Two Issuance Flows

The app supports two different credential delivery methods:

#### Authorization Flow
- Uses OAuth 2.0 authorization code grant
- Recipient must authenticate and authorize credential issuance
- More explicit user consent

#### Pre-Authorized Flow
- Uses pre-authorized code grant
- Credential offer generated without prior authentication
- Simpler, more direct delivery

### Wallet Agent Integration

Currently, the app integrates with two wallet agent providers:
- **Sphereon** (authorization flow)
- **Unime/Impierce** (pre-authorized flow)

**Important Note**: The differences between vendors are largely a proof-of-concept artifact and interoperability workaround. As the OID4VCI specification matures and wallet implementations converge, the goal is to have a single issuer endpoint that can serve credentials to **all wallets that follow the standard**, regardless of vendor.

## Open Badges 3.0 Features

The OB3 integration supports key edubadges features in the verifiable credential format:

### Educational Extensions
- **ECTS Credits**: European Credit Transfer System values
- **Language**: Language of instruction
- **Education Program Identifier**: Links to specific programs (e.g., CROHO codes)
- **Participation Type**: How learning occurred (online, blended, on-campus)

### Alignment
Links credentials to external taxonomies and frameworks (e.g., ESCO skills taxonomy), enabling better credential recognition and validation.

### Privacy-Preserving Identity
Recipient identifiers are hashed with a salt, allowing credential ownership verification without exposing personal information like email addresses.

## Deployment

### Production Edubadges

Production Edubadges has this feature disabled and does not have an issuer.

### Demo Environment

A demonstration issuer is available for:
- Testing the end-to-end credential flow
- Showcasing capabilities to stakeholders
- Training new institutions considering OB3 adoption

But this does not focus on interop, all verifiable credential features and formats. Just the most simple version.

### Production: EWI Project on SDP

The OB3 integration is deployed in development on **SURF Development Platform (SDP)**, and will be deployed in production on **SURF Development Platform (SDP)** too. 
Where this "production" is only used in the context of the Pilots in the SURF and NPULS EWI project.

This focuses on interoperability with other verifiable credential formats and systems and flows, such as OID4VCI authorized code flow and more.

## API Usage

### Issuing a Credential

To issue an OB 3.0 credential from an existing badge:

```http
POST /v1/ob3
Content-Type: application/json
Authorization: Bearer <user_token>

{
  "badge_id": "abc123-def456-ghi789",
  "variant": "authorization"
}
```

**Response:**
```json
{
  "offer": "openid-credential-offer://..."
}
```

The offer can be:
- Displayed as a QR code for mobile wallet apps
- Used as a deep link to launch wallet applications
- Shared via other channels

### What Gets Issued

The credential includes:
- All badge information (name, description, criteria, image)
- Issuer details
- Educational metadata (ECTS, language, alignments)
- Validity dates
- Privacy-preserving recipient identifier

## Configuration

Required environment variables:

```bash
# Sphereon wallet agent (authorization flow)
OB3_AGENT_URL_SPHEREON=https://agent.sphereon.com/...
OB3_AGENT_AUTHZ_TOKEN_SPHEREON=bearer_token_here

# Unime/Impierce wallet agent (pre-authorized flow)
OB3_AGENT_URL_UNIME=https://agent.unime.it/...
```

## Future Direction

### Short-Term Improvements
- Full eduID integration for better identity handling
- Enhanced support for eduPerson attributes (ePPN)
- Unified wallet agent interface as standards mature

### Long-Term Vision

As the OID4VCI specification stabilizes and wallet implementations converge on the standard, the multiple vendor-specific integrations will consolidate into a single, standard-compliant issuer endpoint. This will allow any spec-compliant wallet to receive edubadges credentials without vendor-specific code paths.

The goal is full interoperability: issue once, receive anywhere.

## Testing

Run the OB3 test suite:

```bash
python manage.py test apps.ob3
```

Tests cover credential structure, extension handling, privacy features, and serialization logic.

## References

- [Open Badges 3.0 Specification](https://www.imsglobal.org/spec/ob/v3p0/)
- [OpenID for Verifiable Credential Issuance](https://openid.net/specs/openid-4-verifiable-credential-issuance-1_0.html)
- [Edubadges Documentation](https://www.surf.nl/en/edubadges-national-approach-to-badges-in-education)
- [European Digital Identity Wallet](https://ec.europa.eu/digital-building-blocks/wikis/display/DIGITAL/EUDI+Wallet)