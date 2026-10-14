# file: fastapi/fastapi/encoders.py:102-343
# asked: {"lines": [209, 210, 211, 213, 215, 220, 221, 222, 234, 257, 259, 321], "branches": [[206, 209], [209, 210], [209, 212], [210, 209], [210, 211], [212, 213], [214, 215], [219, 220], [221, 222], [221, 223], [233, 234], [256, 257], [258, 259], [320, 321]]}
# gained: {"lines": [213, 215, 257, 259, 321], "branches": [[212, 213], [214, 215], [256, 257], [258, 259], [320, 321]]}

import pytest
from pydantic import BaseModel, RootModel
from enum import Enum
from pathlib import PurePath
from collections import deque
from fastapi.encoders import jsonable_encoder

class CustomEnum(Enum):
    OPTION_A = "Option A"
    OPTION_B = "Option B"

class SampleModel(BaseModel):
    field1: str
    field2: int

def test_custom_encoder():
    class CustomClass:
        pass

    def custom_encoder(obj):
        return "custom_encoded"

    obj = CustomClass()
    result = jsonable_encoder(obj, custom_encoder={CustomClass: custom_encoder})
    assert result == "custom_encoded"

def test_include_set_conversion():
    obj = SampleModel(field1="value1", field2=2)
    result = jsonable_encoder(obj, include=["field1"])
    assert result == {"field1": "value1"}

def test_exclude_set_conversion():
    obj = SampleModel(field1="value1", field2=2)
    result = jsonable_encoder(obj, exclude=["field2"])
    assert result == {"field1": "value1"}

def test_pydantic_v1_encoders():
    class SampleModelV1(BaseModel):
        field1: str
        field2: int

        class Config:
            json_encoders = {int: lambda v: f"int_{v}"}

    obj = SampleModelV1(field1="value1", field2=2)
    result = jsonable_encoder(obj)
    assert result == {"field1": "value1", "field2": "int_2"}

def test_root_key_handling():
    class RootStrModel(RootModel[str]):
        pass

    obj = RootStrModel(root="root_value")
    result = jsonable_encoder(obj)
    assert result == "root_value"

def test_enum_handling():
    obj = CustomEnum.OPTION_A
    result = jsonable_encoder(obj)
    assert result == "Option A"

def test_purepath_handling():
    obj = PurePath("/some/path")
    result = jsonable_encoder(obj)
    assert result == "/some/path"

def test_encoders_by_class_tuples(monkeypatch):
    class CustomClass:
        pass

    def custom_encoder(obj):
        return "encoded_by_class"

    encoders_by_class_tuples = {custom_encoder: (CustomClass,)}
    monkeypatch.setattr('fastapi.encoders.encoders_by_class_tuples', encoders_by_class_tuples)

    obj = CustomClass()
    result = jsonable_encoder(obj)
    assert result == "encoded_by_class"

@pytest.fixture(autouse=True)
def run_around_tests(monkeypatch):
    # Setup: clear any global state or configurations
    monkeypatch.setattr('fastapi.encoders.encoders_by_class_tuples', {})
    yield
    # Teardown: reset any changes made during tests
    monkeypatch.undo()
