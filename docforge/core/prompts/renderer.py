"""Prompt template rendering with Jinja2."""

from typing import Any, Dict, Optional

from jinja2 import Environment, Template, TemplateSyntaxError, UndefinedError

from docforge.core.prompts.models import PromptDefinition


class PromptRenderer:
    """Renders prompt templates with context variables.
    
    Uses Jinja2 for flexible, powerful templating.
    """

    def __init__(self) -> None:
        """Initialize Jinja2 environment."""
        self.env = Environment(
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render(
        self,
        prompt_def: PromptDefinition,
        context: Dict[str, Any],
        strict: bool = False,
    ) -> str:
        """Render a prompt template with context.
        
        Args:
            prompt_def: Prompt definition with template
            context: Variables to substitute into template
            strict: If True, raise on undefined variables;
                   if False, leave them as-is
            
        Returns:
            Rendered prompt string
            
        Raises:
            TemplateSyntaxError: If template has invalid syntax
            UndefinedError: If strict=True and undefined var referenced
        """
        try:
            template = self.env.from_string(prompt_def.template)
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Invalid template syntax in {prompt_def.name}: {e.message}",
                e.lineno,
                e.name,
                e.filename,
            )

        try:
            if strict:
                return template.render(context)
            else:
                # Use undefined behavior that leaves variables in place
                from jinja2 import DebugUndefined
                template.environment.undefined = DebugUndefined
                return template.render(context)
        except UndefinedError as e:
            if strict:
                raise UndefinedError(
                    f"Undefined variable in {prompt_def.name}: {e.message}"
                )
            return template.render(context)

    def validate_template(self, template_str: str) -> bool:
        """Check if template string is valid Jinja2.
        
        Args:
            template_str: Template to validate
            
        Returns:
            True if template is valid, False otherwise
        """
        try:
            self.env.from_string(template_str)
            return True
        except TemplateSyntaxError:
            return False
