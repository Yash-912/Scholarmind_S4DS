"""
Prompt Registry — Versioned prompt templates with Jinja2 rendering.
"""

import json
import os
from jinja2 import Template
from typing import Optional
from datetime import datetime


# Prompt template directory
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


class PromptRegistry:
    """
    Manages versioned prompt templates.
    Templates stored as JSON files with Jinja2 template strings.
    """

    def __init__(self):
        self._templates: dict[str, dict] = {}
        self._loaded = False

    def load(self):
        """Load all prompt templates from disk."""
        if self._loaded:
            return

        os.makedirs(PROMPTS_DIR, exist_ok=True)

        # Load built-in templates
        self._register_builtins()

        # Load custom templates from disk
        for filename in os.listdir(PROMPTS_DIR):
            if filename.endswith(".json"):
                filepath = os.path.join(PROMPTS_DIR, filename)
                try:
                    with open(filepath, "r") as f:
                        template_data = json.load(f)
                        name = template_data.get("name", filename.replace(".json", ""))
                        self._templates[name] = template_data
                except Exception as e:
                    print(f"⚠️ Failed to load prompt {filename}: {e}")

        self._loaded = True
        print(f"✅ Loaded {len(self._templates)} prompt templates")

    def _register_builtins(self):
        """Register built-in prompt templates."""

        self._templates["synthesis"] = {
            "name": "synthesis",
            "version": "1.0",
            "description": "Multi-paper synthesis prompt",
            "system": "You are ScholarMind, an AI research assistant that synthesizes scientific papers. You always cite your sources using [Paper N] notation. You are precise, thorough, and highlight areas of agreement and disagreement between papers.",
            "template": """Based on the following research papers, provide a comprehensive synthesis answering the question: "{{ query }}"

{% for paper in papers %}
[Paper {{ loop.index }}] {{ paper.title }}
{{ paper.text }}

{% endfor %}

Provide your synthesis in the following format:

## Key Findings
Summarize the main discoveries and contributions across all papers.

## Methodology Comparison
Compare the approaches used across different papers.

## Points of Agreement
Where do the papers converge?

## Points of Disagreement or Open Questions
Where do they diverge? What remains unresolved?

## Research Gaps
What areas need further investigation?

Always cite specific papers using [Paper N] notation.""",
        }

        self._templates["comparison"] = {
            "name": "comparison",
            "version": "1.0",
            "description": "Side-by-side paper comparison",
            "system": "You are ScholarMind, an AI research assistant. Provide structured, objective comparisons between research papers.",
            "template": """Compare the following research papers on: "{{ query }}"

{% for paper in papers %}
[Paper {{ loop.index }}] {{ paper.title }}
{{ paper.text }}

{% endfor %}

Provide a structured comparison:

## Overview
Brief summary of what each paper contributes.

## Comparison Table
| Aspect | {% for paper in papers %}Paper {{ loop.index }} | {% endfor %}
|--------|{% for paper in papers %}------------|{% endfor %}
| Method | {% for paper in papers %} | {% endfor %}
| Data | {% for paper in papers %} | {% endfor %}
| Results | {% for paper in papers %} | {% endfor %}

## Strengths and Weaknesses
For each paper, note strengths and limitations.

## Recommendation
Which approach is most promising and why?""",
        }

        self._templates["gap_analysis"] = {
            "name": "gap_analysis",
            "version": "1.0",
            "description": "Research gap identification",
            "system": "You are ScholarMind. You identify gaps and opportunities in research fields by analyzing existing work.",
            "template": """Analyze the following papers to identify research gaps related to: "{{ query }}"

{% for paper in papers %}
[Paper {{ loop.index }}] {{ paper.title }}
{{ paper.text }}

{% endfor %}

## Covered Ground
What has been well-studied based on these papers?

## Identified Gaps
What important questions remain unanswered?

## Suggested Directions
What specific research studies could fill these gaps?

## Cross-Disciplinary Opportunities
Are there techniques from other fields that could be applied?""",
        }

        self._templates["summarize_single"] = {
            "name": "summarize_single",
            "version": "1.0",
            "description": "Single paper summary",
            "system": "You are ScholarMind. Provide clear, structured summaries of research papers.",
            "template": """Summarize the following research paper:

Title: {{ title }}
Abstract: {{ abstract }}

Provide:
1. **One-line summary**: What is this paper about in one sentence?
2. **Problem**: What problem does this paper address?
3. **Approach**: What method/approach do they use?
4. **Key Results**: What are the main findings?
5. **Significance**: Why does this matter?
6. **Limitations**: What are the limitations noted?""",
        }

        self._templates["chat"] = {
            "name": "chat",
            "version": "1.0",
            "description": "General research chat/QA",
            "system": "You are ScholarMind, an AI research assistant. Answer questions about research papers accurately and cite your sources.",
            "template": """{% if papers %}Based on these retrieved papers:

{% for paper in papers %}
[Paper {{ loop.index }}] {{ paper.title }}
{{ paper.text }}

{% endfor %}
{% endif %}

User question: {{ query }}

Provide a helpful, well-cited answer.""",
        }

    def render(
        self,
        template_name: str,
        **kwargs,
    ) -> tuple[str, str, str]:
        """
        Render a prompt template.

        Args:
            template_name: Name of the template
            **kwargs: Template variables

        Returns:
            Tuple of (rendered_prompt, system_prompt, version)
        """
        if not self._loaded:
            self.load()

        template_data = self._templates.get(template_name)
        if not template_data:
            raise ValueError(f"Unknown prompt template: {template_name}")

        template = Template(template_data.get("template") or template_data.get("user_template", "{{ query }}"))
        rendered = template.render(**kwargs)
        system_prompt = template_data.get("system", "")
        version = template_data.get("version", "1.0")

        return rendered, system_prompt, version

    def list_templates(self) -> list[dict]:
        """List all available templates."""
        if not self._loaded:
            self.load()

        return [
            {
                "name": t["name"],
                "version": t.get("version", "1.0"),
                "description": t.get("description", ""),
            }
            for t in self._templates.values()
        ]

    def get_template(self, name: str) -> Optional[dict]:
        """Get a specific template."""
        if not self._loaded:
            self.load()
        return self._templates.get(name)


# Global singleton
prompt_registry = PromptRegistry()
