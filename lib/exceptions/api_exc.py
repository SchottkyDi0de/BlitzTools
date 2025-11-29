class ApiError(Exception):
    """Base class for API errors."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class FieldNotSpecifiedError(ApiError):
    def __init__(self, field):
        super().__init__(f"{field}_NOT_SPECIFIED: Не заполнено обязательное поле {field}.")


class FieldNotFoundError(ApiError):
    def __init__(self, field):
        super().__init__(f"{field}_NOT_FOUND: Информация не найдена.")


class MethodNotFoundError(ApiError):
    def __init__(self):
        super().__init__("METHOD_NOT_FOUND: Указан неверный метод API.")


class MethodDisabledError(ApiError):
    def __init__(self):
        super().__init__("METHOD_DISABLED: Указаный метод API отключён.")


class FieldListLimitExceededError(ApiError):
    def __init__(self, field):
        super().__init__(f"{field}_LIST_LIMIT_EXCEEDED: Превышен лимит переданных идентификаторов в поле {field}.")


class ApplicationIsBlockedError(ApiError):
    def __init__(self):
        super().__init__("APPLICATION_IS_BLOCKED: Приложение заблокировано администрацией.")


class InvalidFieldError(ApiError):
    def __init__(self, field):
        super().__init__(f"INVALID_{field}: Указано не валидное значение параметра {field}.")


class InvalidApplicationIdError(ApiError):
    def __init__(self):
        super().__init__("INVALID_APPLICATION_ID: Неверный идентификатор приложения.")


class InvalidIpAddressError(ApiError):
    def __init__(self):
        super().__init__("INVALID_IP_ADDRESS: Недопустимый IP-адрес для серверного приложения.")


class RequestLimitExceededError(ApiError):
    def __init__(self):
        super().__init__("REQUEST_LIMIT_EXCEEDED: Превышены лимиты квотирования.")


class SourceNotAvailableError(ApiError):
    def __init__(self):
        super().__init__("SOURCE_NOT_AVAILABLE: Источник данных не доступен.")