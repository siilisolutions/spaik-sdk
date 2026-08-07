import pytest

from spaik_sdk.models.providers.azure_deployments import AZURE_DEPLOYMENT_ENV_VARS, get_deployment_name


@pytest.mark.unit
class TestAzureDeployments:
    @pytest.mark.parametrize(
        "model_name,env_var",
        [
            ("gpt-5.6-sol", "AZURE_GPT_5_6_SOL_DEPLOYMENT"),
            ("gpt-5.6-terra", "AZURE_GPT_5_6_TERRA_DEPLOYMENT"),
            ("gpt-5.6-luna", "AZURE_GPT_5_6_LUNA_DEPLOYMENT"),
        ],
    )
    def test_gpt_5_6_models_have_azure_env_vars(self, model_name: str, env_var: str):
        assert AZURE_DEPLOYMENT_ENV_VARS[model_name] == env_var
        assert get_deployment_name(model_name) == model_name

    def test_unsupported_model_raises(self):
        with pytest.raises(ValueError, match="not supported on Azure"):
            get_deployment_name("claude-fable-5")
