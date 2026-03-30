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
import logging
from string import Template

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PromptTemplate(BaseModel):
    """A reusable prompt template with variable substitution.

    Uses Python string.Template syntax ($variable or ${variable}).
    """

    name: str
    template: str
    description: str = ""
    version: str = "1.0"
    metadata: dict = Field(default_factory=dict)

    def render(self, **variables) -> str:
        """Render the template with the given variables.

        Args:
            **variables: Key-value pairs to substitute into the template.

        Returns:
            The rendered prompt string.

        Raises:
            KeyError: If a required template variable is missing.
        """
        return Template(self.template).substitute(**variables)

    def safe_render(self, **variables) -> str:
        """Render the template, leaving unresolved variables in place.

        Args:
            **variables: Key-value pairs to substitute into the template.

        Returns:
            The rendered prompt string with unresolved variables intact.
        """
        return Template(self.template).safe_substitute(**variables)


class PromptManager:
    """Manages a registry of prompt templates for GenAI pipelines.

    Provides registration, retrieval, and rendering of versioned prompt
    templates. Templates are stored in-memory and can be loaded from
    configuration or registered programmatically.
    """

    def __init__(self):
        self._templates: dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate) -> None:
        """Register a prompt template.

        Args:
            template: The prompt template to register.
        """
        key = f"{template.name}:{template.version}"
        self._templates[key] = template
        logger.info("Registered prompt template '%s' (v%s)", template.name, template.version)

    def get(self, name: str, version: str = "1.0") -> PromptTemplate:
        """Retrieve a registered prompt template.

        Args:
            name: Template name.
            version: Template version.

        Returns:
            The matching PromptTemplate.

        Raises:
            KeyError: If no template matches the name and version.
        """
        key = f"{name}:{version}"
        if key not in self._templates:
            raise KeyError(f"Prompt template '{name}' version '{version}' not found")
        return self._templates[key]

    def render(self, name: str, version: str = "1.0", **variables) -> str:
        """Retrieve and render a prompt template in one call.

        Args:
            name: Template name.
            version: Template version.
            **variables: Variables to substitute.

        Returns:
            The rendered prompt string.
        """
        template = self.get(name, version)
        return template.render(**variables)

    def list_templates(self) -> list[PromptTemplate]:
        """Return all registered prompt templates."""
        return list(self._templates.values())

    def remove(self, name: str, version: str = "1.0") -> bool:
        """Remove a prompt template from the registry.

        Args:
            name: Template name.
            version: Template version.

        Returns:
            True if the template was removed, False if not found.
        """
        key = f"{name}:{version}"
        if key in self._templates:
            del self._templates[key]
            logger.info("Removed prompt template '%s' (v%s)", name, version)
            return True
        return False
