"""Исключения взаимодействия модулей."""

class IntegrationError(Exception):
    """Базовая ошибка взаимодействия модулей. exit_code — код возврата программы."""

    exit_code = 1

class InvalidDataError(IntegrationError):
    """Некорректные данные на входе или выходе модуля."""

    exit_code = 1
