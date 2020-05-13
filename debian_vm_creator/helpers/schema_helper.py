import cerberus
import validators

from .exception_helper import AppException
from .yaml_helper import yaml_dump


class BaseValidationException(AppException):
    def __init__(self, errors):
        super().__init__(yaml_dump(errors).strip())


class SchemaValidationException(BaseValidationException):
    pass


class DocumentValidationException(BaseValidationException):
    pass


def validate(schema, document):
    try:
        validator = cerberus.Validator(schema, require_all=True)
    except cerberus.schema.SchemaError as error:
        (errors,) = error.args
        raise SchemaValidationException(errors)

    if validator.validate(document):
        return validator.document

    raise DocumentValidationException(validator.errors)


def is_url_check(field, value, error):
    if not validators.url(value):
        error(field, "must be a valid URL")


def is_domain_check(field, value, error):
    if not validators.domain(value):
        error(field, "must be a valid domain name")


def is_ipv4_check(field, value, error):
    if not validators.ipv4(value):
        error(field, "must be a valid ipv4 address")


def is_ipv4_cidr_check(field, value, error):
    if not validators.ipv4_cidr(value):
        error(field, "must be a valid ipv4 cidr")


def is_mac_address_check(field, value, error):
    if not validators.mac_address(value):
        error(field, "must be a valid mac address")


MANDATORY_STRING_RULE = {"type": "string", "empty": False}

OPTIONAL_STRING_RULE = {"type": "string", "empty": True}

POSITIVE_INTEGER_RULE = {"type": "integer", "min": 1}

BOOLEAN_RULE = {"type": "boolean"}

URL_STRING_RULE = {"type": "string", "check_with": is_url_check}

DOMAIN_STRING_RULE = {"type": "string", "check_with": is_domain_check}

IPV4_STRING_RULE = {"type": "string", "check_with": is_ipv4_check}

MAC_ADDRESS_STRING_RULE = {"type": "string", "check_with": is_mac_address_check}

SALT_RULE = {"master": {"type": "boolean"}, "minion": {"type": "boolean"}}
