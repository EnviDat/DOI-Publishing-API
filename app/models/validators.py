"""Custom validators for model fields."""

import logging

from tortoise.exceptions import ValidationError
from tortoise.validators import Validator

log = logging.getLogger(__name__)


class EmptyStringValidator(Validator):
    """Validate whether a string is empty."""

    def __call__(self, value: str):
        """Check value."""
        if not value:
            raise ValidationError("Value can not be empty")
