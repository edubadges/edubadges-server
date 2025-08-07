from django.test import SimpleTestCase
from badgrsocialauth.providers.eduid.oidc_client import EduIdUserInfo

class EduIdUserInfoTest(SimpleTestCase):

    def test_validated_names_in_info(self):
        eppn_json = [
            { 'validated_name': 'Hendrik-Jan Visser' },
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 1)
        self.assertIn('Hendrik-Jan Visser', subject.validated_names())
        
    def test_validated_names_multiple(self):
        eppn_json = [
            { 'validated_name': 'Hendrik-Jan Visser' },
            { 'validated_name': 'Hennie Visser' },
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 2)
        
    def test_validated_names_not_in_info(self):
        eppn_json = [
            { 'name': 'Hendrik-Jan Visser' },
        ]
            
        subject = EduIdUserInfo(eppn_json)
        self.assertEqual(len(subject.validated_names()), 0)