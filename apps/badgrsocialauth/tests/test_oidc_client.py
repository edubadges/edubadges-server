from django.test import SimpleTestCase
from badgrsocialauth.providers.eduid.oidc_client import EduIdUserInfo

class EduIdUserInfoTest(SimpleTestCase):

    def test_validated_names_preferred(self):
        eppn_json = [
            { 'validated_name': 'Hendrik-Jan Visser', 'preferred': False },
            { 'validated_name': 'Hennie Visser', 'preferred': True },
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 1)
        self.assertIn('Hennie Visser', subject.validated_names())
        
    def test_validated_names_multiple(self):
        eppn_json = [
            { 'validated_name': 'Hendrik-Jan Visser', 'preferred': True },
            { 'validated_name': 'Hennie Visser', 'preferred': True },
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 2)
        
    def test_validated_names_not_in_info(self):
        eppn_json = [
            { 'name': 'Hendrik-Jan Visser' }, # no validated_name key
            { 'validated_name': 'Hennie Visser' } # no preferred key
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 0)