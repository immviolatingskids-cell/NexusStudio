"""Expected, actionable failures at the image-execution boundary."""


class ConfigurationError(ValueError):
    pass


class ProviderUnavailableError(RuntimeError):
    pass


class GenerationError(RuntimeError):
    pass


class InvalidProviderResponseError(GenerationError):
    pass


class OutputWriteError(GenerationError):
    pass
