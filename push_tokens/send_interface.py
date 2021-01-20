from exponent_server_sdk import (DeviceNotRegisteredError,
                                 MessageRateExceededError, MessageTooBigError,
                                 PushClient, PushMessage, PushResponseError,
                                 PushServerError)


def send_push_message(token: str, expo_data: dict) -> (str, str):
    expo_data['to'] = token
    expo_data["channel_id"] = "MAX"
    try:
        response = PushClient().publish(PushMessage(**expo_data))
        response.validate_response()
        return 'success', 'Notification sent'
    except (PushResponseError, PushServerError, DeviceNotRegisteredError,
            MessageTooBigError, MessageRateExceededError) as ex:
        return 'error', type(ex).__name__
