from exponent_server_sdk import (
    PushClient, PushMessage,
    PushResponseError,
    DeviceNotRegisteredError,
    MessageRateExceededError,
    MessageTooBigError
)


def send_push_message(token: str, expo_data: dict) -> (str, str):
    expo_data['to'] = token
    expo_data["channel_id"] = "MAX"
    response = PushClient().publish(PushMessage(**expo_data))
    try:
        response.validate_response()
        return 'success', 'Notification sent'
    except (PushResponseError, DeviceNotRegisteredError, MessageTooBigError, MessageRateExceededError) as ex:
        return 'error', type(ex).__name__
