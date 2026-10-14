from coverup.prompt.gpt_v2 import GptV2Prompter

ENVIRONMENT_GUIDANCE = """
IMPORTANT ENVIRONMENT INFORMATION:
- Python 3.10.9
- Pydantic 2.14.1
- Use Pydantic V2 APIs for BaseModel imported from pydantic.
- Use pydantic.v1 explicitly for Pydantic V1 behavior.
- Do not use legacy __config__ assignments on Pydantic V2 models.
- Import all referenced symbols.
- Verify assertions against actual implementation behavior.
"""

REPAIR_GUIDANCE = """
IMPORTANT REPAIR REQUIREMENTS:
- Pydantic version is 2.14.1.
- Check for Pydantic V1/V2 API incompatibilities.
- Fix imports and model configuration before changing assertions.
- Preserve meaningful assertions and coverage improvement.
"""

_original_initial = GptV2Prompter.initial_prompt
_original_error = GptV2Prompter.error_prompt


def enhanced_initial(self, segment):
    messages = _original_initial(self, segment)
    messages[0]["content"] += "\n" + ENVIRONMENT_GUIDANCE
    return messages


def enhanced_error(self, segment, error):
    messages = _original_error(self, segment, error)
    if messages is not None:
        messages[0]["content"] += "\n" + REPAIR_GUIDANCE
    return messages


GptV2Prompter.initial_prompt = enhanced_initial
GptV2Prompter.error_prompt = enhanced_error
