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
}
