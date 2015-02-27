"""
This file contains JSON badge resources needed for specific tests, with documentation
on the particular errors or challenges each example presents.
"""

# Null expiration date assertion. "expires" is an optional field. If present it should not be null
null_expires_assertion = """
{
    "recipient": "sha256$1a29bbe7d65355ce7647793396041c7bebbe333e677222c5ca116f5cc038b9ef",
    "verify": {
        "type": "hosted",
        "url": "http://app.achievery.com/badge-assertion/4613"
    },
    "uid": "4613",
    "issuedOn": "2014-09-05",
    "expires": null,
    "badge": {
        "name": "DPD Project Contributor",
        "description": "Awarded for team members on the DPD project that studied badge system design from 2012-2014.",
        "image": "https://images.achievery.com/badgeImages/DPDContributorBadge_1716_1.png",
        "tags": [
            "Higher Education",
            "Writing"
        ],
        "issuer": {
            "name": "Design Principles Documentation Project",
            "image": "https://images.achievery.com/organization/badger-icon-transparent.png",
            "url": "http://app.achievery.com/passport/id/2515",
            "_location": "http://app.achievery.com/badge-issuer/1716",
            "origin": "http://app.achievery.com"
        },
        "criteria": "http://app.achievery.com/badge/1716",
        "alignment": [
            {
                "name": "DPD Project Website",
                "url": "http://dpdproject.info",
                "description": "The homepage for the DPD Project showcases design principles for using digital badges for learning, related research literature, analysis of common challenges, and badge system design tools developed by the team."
            }
        ],
        "_location": "http://app.achievery.com/badge-class/1716"
    },
    "evidence": "http://app.achievery.com/badge-earned/4613",
    "image": "https://images.achievery.com/badgeImages/DPDContributorBadge_1716_1.png",
    "_originalRecipient": {
        "type": "email",
        "hashed": true,
        "salt": "2zjIsSSl12PiZJkiq4Hq33ImLFhHMBHBrSzDyc9DiOtGVg8P7VDVPNa2QgAXHQQ9",
        "identity": "sha256$1a29bbe7d65355ce7647793396041c7bebbe333e677222c5ca116f5cc038b9ef"
    },
    "salt": "2zjIsSSl12PiZJkiq4Hq33ImLFhHMBHBrSzDyc9DiOtGVg8P7VDVPNa2QgAXHQQ9",
    "issued_on": "2014-09-05T21:45:09.000Z"
}
"""

# In late 2013-late 2014 the Mozilla Backpack was baking this strange nested pseudo-0.5 
# representation of a badge instead of the original assertion. Implementations should fetch
# the original assertion and validate that instead of dealing with this.
backpack_misbake_assertion = {
    "uid": "100",
    "issuedOn": 1395112143,
    "recipient": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
    "evidence": "http://someevidence.org",
    "verify": {
        "url": "http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100",
        "type": "hosted"
    },
    "badge": {
        "issuer": {
            "url": "http://schoolofdata.org",
            "image": "http://assets.okfn.org/p/schoolofdata/img/logo.png",
            "name": "School of Data",
            "email": "michael.bauer@okfn.org",
            "contact": "michael.bauer@okfn.org",
            "revocationList": "http://badges.schoolofdata.org/revocation",
            "description": "School of Data works to empower civil society organizations, journalists and citizens with the skills they need to use data effectively-evidence is power!",
            "_location": "http://badges.schoolofdata.org/issuer/school-of-data",
            "origin": "http://schoolofdata.org"
        },
        "description": "You have completed the Data to Diagrams module on the School of Data",
        "image": "http://p2pu.schoolofdata.org/badges/School_Of_Data_Badges/Badges/Badge_Data_to_Diagrams.png",
        "criteria": "http://badges.schoolofdata.org/badge/data-to-diagrams/criteria",
        "name": "Data to Diagrams",
        "_location": "http://badges.schoolofdata.org/badge/data-to-diagrams"
    },
    "_originalRecipient": {
        "identity": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
        "type": "email",
        "hashed": True
    },
    "issued_on": 1395112143
}
# The original theoretical hosted assertion for the backpack_misbake_assertion
backpack_misbake_original_assertion = {
    "evidence": "http://someevidence.org",
    "recipient": {
        "hashed": True,
        "identity": "sha256$c56e0383f16d3bd4705c11e4eff7002ca27540b2ba0b32d7b389377f9e4d68e2",
        "type": "email"
    },
    "uid": "100",
    "badge": "http://badges.schoolofdata.org/badge/data-to-diagrams",
    "verify": {
        "url": "http://badges.schoolofdata.org/badge/data-to-diagrams/instance/100",
        "type": "hosted"
    },
    "issuedOn": 1395112143
}
# The other resources for the backpack_misbake_original_assertion
backpack_misbake_original_badgeclass = {
    "criteria": "http://badges.schoolofdata.org/badge/data-to-diagrams/criteria",
    "issuer": "http://badges.schoolofdata.org/issuer/school-of-data",
    "description": "You have completed the \"Data to Diagrams\" module on the School of Data",
    "name": "Data to Diagrams",
    "image": "http://p2pu.schoolofdata.org/badges/School_Of_Data_Badges/Badges/Badge_Data_to_Diagrams.png"
}
backpack_misbake_original_issuerorg = {
    "description": "School of Data works to empower civil society organizations",
    "image": "http://assets.okfn.org/p/schoolofdata/img/logo.png",
    "revocationList": "http://badges.schoolofdata.org/revocation",
    "contact": "michael.bauer@okfn.org", "email": "michael.bauer@okfn.org",
    "url": "http://schoolofdata.org",
    "name": "School of Data"
}


# A valid 1.0 badge
valid_1_0_assertion = {
    "uid": "2f900c7c-f473-4bff-8173-71b57472a97f",
    "recipient": {
        "identity": "sha256$1665bc8985e802067453647c1676b07a1834c327bfea24c67f3dbb721eb84d22",
        "type": "email",
        "hashed": True,
        "salt": "UYMA1ybJ4UfqHJO4r3x7LjpGE0LEog"
    },
    "badge": "http://openbadges.oregonbadgealliance.org/api/badges/53d727a11f04f3a84a99b002",
    "verify": {
        "type": "hosted",
        "url": "http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205"
    },
    "issuedOn": 1406747839,
    "image": "http://openbadges.oregonbadgealliance.org/api/assertions/53d944bf1400005600451205/image"
}
valid_1_0_badgeclass = {
    "_id": {"$oid": "53d727a11f04f3a84a99b002"},
    "name": "Oregon Open Badges Working Group Initial Meeting",
    "description": "Invited participant to the first meeting of Oregon's Open Badges Working Group in July 2014.",
    "image": "http://placekitten.com/300/300",
    "criteria": "http://openbadges.oregonbadgealliance.org/assets/criteria/obwg-initial-meeting.html",
    "issuer": "http://openbadges.oregonbadgealliance.org/api/issuers/53d41603f93ae94a733ae554",
    "tags": ["participation"]
}
valid_1_0_issuer = {
    "_id": {"$oid": "53d41603f93ae94a733ae554"},
    "name": "Oregon Badge Alliance",
    "url": "http://oregonbadgealliance.org",
    "description": "The Oregon Badge Alliance serves as a focal point for collaborations between state institutions, employers, and the education community as we work together to build a vibrant ecosystem for badges and micro-certifications in Oregon.",
    "email": "oregonbadgealliance@gmail.com",
    "fullyQualifiedUrl": "http://openbadges.oregonbadgealliance.org/api/issuers/53d41603f93ae94a733ae554"
}


# A couple assertions of a valid 1.1 badge, and their supporting resources
simpleOneOne = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "http://example.org/assertion25",
    "uid": '25',
    "recipient": {
        "identity": "testuser@example.org",
        "type": "email",
        "hashed": False
    },
    "badge": "http://example.org/badge1",
    "verify": {
        "type": "hosted",
        "url": "http://example.org/assertion25"
    },
    "issuedOn": "2014-01-31"
}
simpleOneOneTwo = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "http://example.org/assertion30",
    "uid": '30',
    "recipient": {
        "identity": "testuser@example.org",
        "type": "email",
        "hashed": False
    },
    "badge": "http://example.org/badge1",
    "verify": {
        "type": "hosted",
        "url": "http://example.org/assertion25"
    },
    "issuedOn": "2014-01-31"
}
simpleOneOneBC = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "badgeclass",
    "@id": "http://example.org/badge1",
    "name": "Badge of Awesome",
    "description": "Awesomest badge for awesome people.",
    "image": "http://placekitten.com/300/300",
    "criteria": "http://example.org/badge1criteria",
    "issuer": "http://example.org/issuer"
}
simpleOneOneIssuer = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "issuerorg",
    "@id": "http://example.org/issuer",
    "name": "Issuer of Awesome",
    "url": "http://example.org"
}


# A 1.1 style badge with an array for the JSON-LD @type instead of a single entry
oneOneArrayType = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": ["assertion", "http://othertype.com/type"],
    "@id": "http://example.org/assertion25",
    "uid": '25'
}

# A 1.1 assertion with an ID that is not recognizable as a dereferencable IRI or compact IRI within the OBI context
oneOneNonUrlID = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "@id": "assertion25",
    "uid": '25'
}

# A 1.1 assertion without the required @id property but with the correct IRI in the verify.url property
simpleOneOneNoId = {
    "@context": "http://standard.openbadges.org/1.1/context.json",
    "@type": "assertion",
    "verify": {"type": "hosted", "url": "http://example.org/assertion25"},
    "uid": '25'
}
