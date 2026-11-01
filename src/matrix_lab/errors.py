"""Исключения взаимодействия модулей."""


class IntegrationError(Exception):
    """Базовая ошибка взаимодействия модулей. exit_code — код возврата программы."""

    exit_code = 1


class InvalidDataError(IntegrationError):
    """Некорректные данные на входе или выходе модуля."""

    exit_code = 1


class ModuleUnavailableError(IntegrationError):
    """Модуль (сервис) недоступен: отказ в соединении, обрыв связи."""

    exit_code = 2


class ModuleTimeoutError(IntegrationError):
    """Модуль не ответил за отведённое время."""

    exit_code = 3


class VersionConflictError(IntegrationError):
    """Версии API взаимодействующих модулей несовместимы."""

    exit_code = 4
