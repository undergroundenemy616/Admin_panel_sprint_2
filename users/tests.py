from django.test import TestCase
from users.models import User


class UserClassTestCase(TestCase):
    def test_correct_phone_number(self):
        method = User.normalize_phone

        phone_number_0 = '89098357415'
        phone_number_1 = '+79098357415'
        phone_number_2 = '+89098357415'
        phone_number_3 = '2139098357415'
        phone_number_4 = '+572139098357415'
        phone_number_5 = '572139098357415'

        self.assertEqual(method(phone_number_0), '+79098357415')
        self.assertEqual(method(phone_number_1), '+79098357415')
        self.assertEqual(method(phone_number_2), '+79098357415')
        self.assertEqual(method(phone_number_3), '+2139098357415')
        self.assertEqual(method(phone_number_4), '+572139098357415')
        self.assertEqual(method(phone_number_5), '+572139098357415')

    def test_incorrect_phone_number(self):
        method = User.normalize_phone

        phone_number_0 = '9098357415'
        phone_number_1 = '098357415'
        phone_number_2 = 'k098357415'
        phone_number_3 = 'k098357415k'
        phone_number_4 = '89098357415+'

        with self.assertRaises(ValueError):
            method(phone_number_0)
        with self.assertRaises(ValueError):
            method(phone_number_1)
        with self.assertRaises(ValueError):
            method(phone_number_2)
        with self.assertRaises(ValueError):
            method(phone_number_3)
        with self.assertRaises(ValueError):
            method(phone_number_4)
