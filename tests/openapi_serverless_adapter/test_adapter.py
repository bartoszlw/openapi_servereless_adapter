import os

from openapi_serverless_adapter.adapter import Adapter, prepare_mapping, read_serverless_config
from petstore_sdk import Pet
from petstore_sdk.api.pet_api import PetApi
from petstore_sdk.configuration import Configuration

sample_mapping = {
    "/orders/{orderId}": "module.package.handler_function",
}

DIR = os.path.dirname(os.path.realpath(__file__))


def test_prepare_mapping():
    out = prepare_mapping(sample_mapping)
    assert out == {"^/orders/(.+)$": ("/orders/{orderId}", ['orderId'], ('module.package', 'handler_function'))}


def test_get_event():
    adapter = Adapter(prepare_mapping(sample_mapping), len('http://google.com'))
    event, handler = adapter.match("http://google.com/orders/123")

    assert event == {
        'resource': '/orders/{orderId}',
        'pathParameters': {'orderId': '123'},
    }
    assert handler == ('module.package', 'handler_function')


def test_get_serverless_handler_mapping():
    mapping = read_serverless_config(DIR + "/serverless.yml")
    assert mapping == {
        "/pet/{petId}": "tests.openapi_serverless_adapter.fixture_lambda.handle_get_pet"
    }


def test_get_with_path_param():
    api = PetApi()
    mapping = prepare_mapping(read_serverless_config(DIR + "/serverless.yml"))
    api.api_client.rest_client = Adapter(mapping, len(Configuration().host))

    pet, status, _ = api.get_pet_by_id_with_http_info(32)

    assert status == 200
    assert pet.__class__ == Pet
    assert pet.name == "petname"
    assert pet.photo_urls[0] == "http://url.com/a.jpg"
    assert len(pet.photo_urls) == 1
