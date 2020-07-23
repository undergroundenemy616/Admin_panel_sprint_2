"""Module only for testing broadcasts service. It will be removed in future."""
import django

django.setup()

from users.broadcasts import SMSBroadcast

if __name__ == '__main__':
    sms_instance = SMSBroadcast(phone_number='89098357415')
    mesg = 'Test from yarik. YOHOO IT IS WORKING'
    response = sms_instance.send(mesg)
    print(sms_instance.is_sent())
    print(response.text)
