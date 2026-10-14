from coverup.prompt.gpt_v2 import GptV2Prompter
from coverup.prompt.prompter import mk_message


ENVIRONMENT_GUIDANCE = """
IMPORTANT ENVIRONMENT INFORMATION:
- Python version: 3.10.9
- Pydantic version: 2.14.1
- FastAPI is imported from the local source checkout.

TEST GENERATION REQUIREMENTS:
1. When using BaseModel from pydantic, follow Pydantic V2 behavior.
2. Do not use __config__ assignments to configure Pydantic V2 models.
3. For Pydantic V1-specific behavior, explicitly import BaseModel
   from pydantic.v1.
4. Import all symbols referenced by generated tests.
5. Verify expected behavior against the actual implementation.
6. Do not invent expected serialization results.
7. Ensure generated tests pass pytest and improve coverage.
"""

REPAIR_GUIDANCE = """
IMPORTANT REPAIR REQUIREMENTS:
- The installed Pydantic version is 2.14.1.
- Check whether the test incorrectly mixes Pydantic V1 and V2 APIs.
- Inspect the relevant implementation using get_info when necessary.
- Fix incorrect imports, configuration, and API usage.
- Do not simply change assertions to match observed outputs.
- Preserve meaningful assertions and coverage improvement.
"""


class CustomGptV2Prompter(GptV2Prompter):

    def initial_prompt(self, segment):
        messages = super().initial_prompt(segment)
        messages[0]["content"] += "\n" + ENVIRONMENT_GUIDANCE
        return messages

    def error_prompt(self, segment, error):
        messages = super().error_prompt(segment, error)
        if messages is not None:
            messages[0]["content"] += "\n" + REPAIR_GUIDANCE
        return messages
