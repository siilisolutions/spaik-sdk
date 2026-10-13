import pytest

from spaik_sdk.models.model_registry import ModelRegistry

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "alias,name",
    [
        ("sonnet", "claude-sonnet-5-5"),
        ("opus", "claude-opus-5-5"),
        ("haiku", "claude-haiku-5-5"),
        ("fable", "claude-fable-5-1"),
        ("gpt", "gpt-6.1-sol"),
        ("gemini flash", "gemini-3.8-flash"),
    ],
)
def test_current_aliases(alias, name):
    assert ModelRegistry.from_name(alias).name == name


@pytest.mark.parametrize("model", list(ModelRegistry.get_all()))
def test_presets_have_exact_identifier_lookup(model):
    assert ModelRegistry.from_name(model.name) == model
    assert model in ModelRegistry.get_by_family(model.family)


def test_unknown_identifier_is_not_a_preset():
    with pytest.raises(ValueError, match="explicit provider"):
        ModelRegistry.from_name("application-deployment")
