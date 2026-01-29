from .error_catalog import DomainError


class MailerError(DomainError):
    pass


class EmailSendError(MailerError):
    """
    Do not register in custom errors!
    """

    pass
