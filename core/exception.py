from rest_framework.views import exception_handler


def detail_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        """
        Get first value in errors dict, and add it to response.
        Values wrapped in list and we extract first value and add it to response dict.
        """
        try:
            error_dict = iter(exc.get_full_details().values())
            error = next(error_dict)
            if isinstance(error, list):
                response.data.update(error[0])
        except AttributeError:
            pass
    return response
