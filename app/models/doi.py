"""Models associated with DOI Database."""

from enum import Enum

from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise import Tortoise

from app.config import config_app
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

        app = config_app.__NAME__
        table = "doi_prefix"


class CkanEntityType(str, Enum):
    """Options for DOI ckan_entity type."""

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
    metadata = fields.CharField(max_length=1000000, validators=[EmptyStringValidator()])
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

        app = config_app.__NAME__
        table = "doi_realisation"
        unique_together = ["prefix_id", "suffix_id"]

#Tortoise.init_models(["app.models.doi"], "models")
DoiPrefixPydantic = pydantic_model_creator(DoiPrefix, name="DoiPrefix")
DoiPrefixInPydantic = pydantic_model_creator(
    DoiPrefix,
    name="DoiPrefixIn",
    exclude_readonly=True,
)
DoiPrefixEditPydantic = pydantic_model_creator(
    DoiPrefix,
    name="DoiPrefixEdit",
    exclude_readonly=True,
    optional=[
        "prefix_id",
        "description",
    ],
)
DoiRealisationPydantic = pydantic_model_creator(DoiRealisation, name="DoiRealisation")
DoiRealisationInPydantic = pydantic_model_creator(
    DoiRealisation,
    name="DoiRealisationIn",
    exclude_readonly=True,
    exclude=["date_created", "date_modified"],
)
DoiRealisationEditPydantic = pydantic_model_creator(
    DoiRealisation,
    name="DoiRealisationEdit",
    exclude_readonly=True,
    optional=[],
    exclude=["date_created", "date_modified"],
)
