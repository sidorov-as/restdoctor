from __future__ import annotations

import copy
import datetime
import typing

import pytest
from django.db.models import TextChoices
from pydantic import BaseModel, Field, StrictInt, StrictStr

from restdoctor.rest_framework.schema.generators import RefsSchemaGenerator
from restdoctor.rest_framework.schema.openapi import RestDoctorSchema
from restdoctor.rest_framework.schema.serializers import (
    OPENAPI_REF_PREFIX,
    pydantic_schema_to_request_filter_parameters,
)
from restdoctor.rest_framework.serializers import PydanticSerializer


class PydanticTestModel(BaseModel):
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    field_a: StrictStr
    field_b: StrictInt
    title: str


class PydanticNestedTestModel(BaseModel):
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    nested_field: PydanticTestModel


class PydanticTestSerializer(PydanticSerializer):
    pydantic_model = PydanticTestModel


class NestedPydanticTestSerializer(PydanticSerializer):
    pydantic_model = PydanticNestedTestModel


class PydanticRequestParamsTestModel(BaseModel):
    field_a: StrictStr = Field(title='field_a', description='Field A')
    field_b: StrictInt | None = Field(None, title='field_b', description='Field B')


@pytest.fixture()
def test_model_schema():
    return {
        'description': 'PydanticTestModel',
        'type': 'object',
        'properties': {
            'created_at': {'description': 'Created At', 'type': 'string', 'format': 'date-time'},
            'field_a': {'description': 'Field A', 'type': 'string'},
            'field_b': {'description': 'Field B', 'type': 'integer'},
            'title': {'description': 'Title', 'type': 'string'},
        },
        'required': ['field_a', 'field_b', 'title'],
    }


@pytest.fixture()
def pydantic_request_params_test_model_as_request_parameters():
    return [
        {
            'name': 'field_a',
            'required': True,
            'in': 'query',
            'schema': {'description': 'Field A', 'type': 'string'},
        },
        {
            'name': 'field_b',
            'required': False,
            'in': 'query',
            'schema': {'description': 'Field B', 'type': 'integer'},
        },
    ]


@pytest.fixture()
def test_nested_model_schema_without_definitions():
    return {
        'description': 'PydanticNestedTestModel',
        'type': 'object',
        'properties': {
            'created_at': {'description': 'Created At', 'type': 'string', 'format': 'date-time'},
            'nested_field': {'$ref': f'{OPENAPI_REF_PREFIX}PydanticTestModel'},
        },
        'required': ['nested_field'],
    }


@pytest.fixture()
def test_nested_model_schema(test_model_schema, test_nested_model_schema_without_definitions):
    schema = copy.deepcopy(test_nested_model_schema_without_definitions)
    schema['properties']['nested_field'] = {'$ref': '#/definitions/PydanticTestModel'}
    schema['definitions'] = {'PydanticTestModel': test_model_schema}
    return schema


def test_get_serializer_schema_success_case(test_model_schema):
    schema = RestDoctorSchema().get_serializer_schema(PydanticTestSerializer())

    assert schema == test_model_schema


def test_map_serializer_without_generator_success_case(test_model_schema):
    schema = RestDoctorSchema().map_serializer(PydanticTestSerializer())

    assert schema == test_model_schema


def test_map_serializer_with_generator_success_case(test_model_schema):
    schema_generator = RefsSchemaGenerator()
    schema = RestDoctorSchema(generator=schema_generator).map_serializer(PydanticTestSerializer())
    ref = f'{OPENAPI_REF_PREFIX}PydanticTestModel'

    assert schema == {'$ref': ref}
    assert schema_generator.local_refs_registry.get_local_ref(ref) == test_model_schema


def test_get_serializer_schema_for_nested_serializer_success_case(test_nested_model_schema):
    schema = RestDoctorSchema().get_serializer_schema(NestedPydanticTestSerializer())

    assert schema == test_nested_model_schema


def test_map_serializer_with_nested_serializer_success_case(test_nested_model_schema):
    schema = RestDoctorSchema().map_serializer(NestedPydanticTestSerializer())

    assert schema == test_nested_model_schema


def test_map_serializer_with_refs_generator_with_nested_serializer_success_case(
    test_nested_model_schema_without_definitions, test_model_schema
):
    schema_generator = RefsSchemaGenerator()
    schema = RestDoctorSchema(generator=schema_generator).map_serializer(
        NestedPydanticTestSerializer()
    )
    ref = f'{OPENAPI_REF_PREFIX}PydanticNestedTestModel'
    nested_ref = test_nested_model_schema_without_definitions['properties']['nested_field']['$ref']

    assert schema == {'$ref': ref}
    assert (
        schema_generator.local_refs_registry.get_local_ref(ref)
        == test_nested_model_schema_without_definitions
    )
    assert schema_generator.local_refs_registry.get_local_ref(nested_ref) == test_model_schema


def test_pydantic_schema_to_request_filter_parameters(
    pydantic_request_params_test_model_as_request_parameters,
):
    schema = PydanticRequestParamsTestModel.schema()

    request_parameters_schema = pydantic_schema_to_request_filter_parameters(schema)

    assert request_parameters_schema == pydantic_request_params_test_model_as_request_parameters
