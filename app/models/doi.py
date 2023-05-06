"""Models associated with DOI Database."""

from enum import Enum

from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator

from app.config import settings
from app.models.validators import EmptyStringValidator


class DoiPrefix(models.Model):
    """The DOI Prefix model."""

    prefix_pk = fields.IntField(pk=True, generated=True)
    prefix_id = fields.CharField(max_length=64, validators=[EmptyStringValidator()])
    description = fields.CharField(max_length=256, null=True)

    def __str__(self):
        """Return the prefix_id as string."""
        return self.prefix_id

    class Meta:
        """Tortoise config."""

        app = settings.APP_NAME


class CkanEntityType(Enum):
    PACKAGE = "package"
    RESOURCE = "resource"


class DoiRealisation(models.Model):
    """The DOI Realisation model."""

    doi_pk = fields.IntField(pk=True, generated=True)
    prefix_id = fields.CharField(max_length=64, validators=[EmptyStringValidator()])
    suffix_id = fields.CharField(max_length=64, validators=[EmptyStringValidator()])
    ckan_id = fields.UUIDField()
    ckan_name = fields.CharField(max_length=256, validators=[EmptyStringValidator()])
    site_id = fields.CharField(max_length=64, validators=[EmptyStringValidator()])
    tag_id = fields.CharField(
        max_length=64, default="envidat.", validators=[EmptyStringValidator()]
    )
    ckan_user = fields.CharField(
        max_length=256, default="admin", validators=[EmptyStringValidator()]
    )
    metadata = fields.CharField(max_length=512, validators=[EmptyStringValidator()])
    metadata_format = fields.CharField(
        max_length=64, default="ckan", validators=[EmptyStringValidator()]
    )
    ckan_entity = fields.data.CharEnumField(CkanEntityType)
    date_created = fields.DatetimeField(auto_now_add=True)
    date_modified = fields.DatetimeField(auto_now=True)

    def __str__(self):
        """Return the combined prefix/suffix DOI combo."""
        return f"{self.prefix_id}/{self.suffix_id}"

    class Meta:
        """Tortoise config."""

        app = settings.APP_NAME


DoiPrefixPydantic = pydantic_model_creator(DoiPrefix, name="DoiPrefix")
DoiPrefixEditPydantic = pydantic_model_creator(
    DoiPrefix,
    name="DoiPrefixEdit",
    exclude_readonly=True,
)
DoiRealisationPydantic = pydantic_model_creator(DoiRealisation, name="DoiRealisation")
DoiRealisationEditPydantic = pydantic_model_creator(
    DoiRealisation,
    name="DoiRealisationEdit",
    exclude_readonly=True,
)
