def normalize(cls, phone_number):
    if not cls.check_phone_len(phone_number):
        msg = 'Phone number must be greater or equal than 12 characters and less or equal than 16 for normalize it!'
        raise ValueError(msg)

    if phone_number.startswith('8') and len(phone_number) == 11 and phone_number.isdigit():
        return '+7' + phone_number[1:]
    elif phone_number.startswith('+7') and len(phone_number) == 12 and phone_number[1:].isdigit():
        return phone_number
    elif phone_number.startswith('+') and phone_number[1:].isdigit():
        return phone_number
    elif phone_number.isdigit():
        return '+' + phone_number
    else:
        msg = 'Phone number must contains only digits and plus character in begin.'
        raise ValueError(msg)
