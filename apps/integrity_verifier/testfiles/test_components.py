test_components = {
'1_0_basic_instance': """{
    "uid":"123abc",
    "recipient": {"identity": "recipient@example.com","hashed": false, "type": "email"},
    "badge": "http://a.com/badgeclass",
    "issuedOn": "2015-04-30",
    "verify": {"type": "hosted", "url": "http://a.com/instance"}
    }""",
'1_0_basic_badgeclass': """{
    "name": "Basic Badge",
    "description": "Basic as it gets. v1.0",
    "image": "http://a.com/badgeclass_image",
    "criteria": "http://a.com/badgeclass_criteria",
    "issuer": "http://a.com/issuer"
    }""",
'1_0_basic_issuer': """{
    "name": "Basic Issuer",
    "url": "http://a.com/issuer"
    }""",

'1_0_instance_with_errors': """{
    "uid":"123abc",
    "recipient": "recipient@example.com",
    "badge": "http://a.com/badgeclass",
    "issuedOn": "2015-04-30",
    "verify": {"type": "hosted", "url": "http://a.com/instance"}
    }""",

'0_5_instance': """{
    "recipient": "recipient@example.com",
    "badge": {
        "version": "0.5.0",
        "name": "Basic McBadge",
        "image": "http://oldstyle.com/images/1",
        "description": "A basic badge.",
        "criteria": "http://oldsyle.com/criteria/1",
        "issuer": {
            "origin": "http://oldstyle.com",
            "name": "Basic Issuer"
        }
    }
    }""",
'0_5_1_instance': """{
    "recipient": "sha256$26051874467e5bc7ad26095cc8876ab2d210835df9cb896b1229af3f9221bf2e",
    "salt": "sel gris",
    "issued_on": "2011-06-01",
    "badge": {
        "version": "0.5.0",
        "name": "Basic McBadge",
        "image": "http://oldstyle.com/images/2",
        "description": "A basic badge.",
        "criteria": "http://oldsyle.com/criteria/2",
        "issuer": {
            "origin": "http://oldstyle.com",
            "name": "Basic Issuer"
        }
    }
    }"""
}
