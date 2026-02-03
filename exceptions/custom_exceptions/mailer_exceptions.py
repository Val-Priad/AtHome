from ..error_catalog import DomainError


class MailerError(DomainError):
    pass


class EmailSendError(MailerError):
    """
    Do not register in custom errors!
    Client doesn't need to know this information,
    registering could lead to enumeration vulnerability.
    """

    pass
