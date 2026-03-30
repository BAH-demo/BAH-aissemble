###
# #%L
# aiSSEMBLE Foundation::GenAI (Python)
# %%
# Copyright (C) 2021 Booz Allen
# %%
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# #L%
###
from pydantic import BaseModel, Field


class TokenUsage(BaseModel):
    """Tracks token consumption for an LLM request."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LlmResponse(BaseModel):
    """Response from an LLM completion request."""

    content: str
    model: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    finish_reason: str = ""
    metadata: dict = Field(default_factory=dict)
