"""Module only for testing broadcasts service. It will be removed in future."""
import django

django.setup()

from users.broadcasts import SMSBroadcast

if __name__ == '__main__':
    phone_num = '89045196397'
    broadcast = SMSBroadcast(phone_number=phone_num)
    text = broadcast.send(message='hello pump')
    print(broadcast.is_sent)
    print(text)
