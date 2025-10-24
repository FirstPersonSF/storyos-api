"""
Transformation Profile Service

Defines how different section types should be transformed by voice application.
Separates transformation strategy from content extraction strategy.
"""
from typing import Dict, Any, Optional
from enum import Enum


class TransformationProfileType(str, Enum):
    """Transformation profile types"""
    PRESERVE = "preserve"
    REDUCE_ONLY = "reduce_only"
    VOICE_CONSTRAINED = "voice_constrained"
    VOICE_FORMATTED = "voice_formatted"
    VOICE_FULL = "voice_full"


class TransformationProfiles:
    """
    Manages transformation profiles and section type mappings.

    Transformation profiles determine HOW voice transformation should be applied
    to different types of content, independent of extraction strategy.
    """

    # Profile Definitions
    PROFILES = {
        TransformationProfileType.PRESERVE: {
            "name": "Preserve",
            "description": "Return content exactly as provided. No transformation.",
            "instructions": (
                "Do not transform this content. Return it exactly as provided, word-for-word. "
                "This content must remain verbatim - it represents quotes or other content that cannot be altered."
            ),
            "preserve_constraints": ["all"],
            "apply_voice": False
        },

        TransformationProfileType.REDUCE_ONLY: {
            "name": "Reduce Only",
            "description": "Preserve voice and meaning. Only reduce length if necessary.",
            "instructions": (
                "Preserve the original voice, tone, and meaning of this content. "
                "Only make changes if the content exceeds length constraints - in that case, reduce length minimally. "
                "Do NOT apply brand voice transformation. Keep the original style intact."
            ),
            "preserve_constraints": ["voice", "meaning"],
            "apply_voice": False
        },

        TransformationProfileType.VOICE_CONSTRAINED: {
            "name": "Voice Constrained",
            "description": "Transform to match brand voice while preserving strict constraints.",
            "instructions": (
                "Transform this content to match the brand voice fully. "
                "CRITICAL: You must preserve the exact length constraint (max words/characters). "
                "The meaning must stay consistent - do not add or remove information. "
                "Apply voice transformation within these strict boundaries."
            ),
            "preserve_constraints": ["length", "meaning"],
            "apply_voice": True
        },

        TransformationProfileType.VOICE_FORMATTED: {
            "name": "Voice Formatted",
            "description": "Transform to match brand voice while maintaining format structure.",
            "instructions": (
                "Transform this content to match the brand voice. "
                "Maintain the list format (bullets, numbers) and item count exactly. "
                "Each list item should be transformed independently. "
                "Preserve the structure while applying voice transformation to the content."
            ),
            "preserve_constraints": ["format", "item_count"],
            "apply_voice": True
        },

        TransformationProfileType.VOICE_FULL: {
            "name": "Voice Full",
            "description": "Full transformation to match brand voice.",
            "instructions": (
                "Transform this content fully to match the brand voice. "
                "Maintain the overall structure and meaning, but apply complete voice transformation. "
                "This includes lexicon, tone, sentence structure, and style. "
                "Ensure the transformed content flows naturally in the brand voice."
            ),
            "preserve_constraints": ["structure", "meaning"],
            "apply_voice": True
        }
    }

    # Section Type Mappings
    # Maps common section names/types to their default transformation profiles
    SECTION_TYPE_MAPPINGS = {
        # Preserve verbatim
        "Quote": TransformationProfileType.PRESERVE,
        "Quote 1": TransformationProfileType.PRESERVE,
        "Quote 2": TransformationProfileType.PRESERVE,
        "Citation": TransformationProfileType.PRESERVE,
        "Attribution": TransformationProfileType.PRESERVE,

        # Minimal transformation
        "Boilerplate": TransformationProfileType.REDUCE_ONLY,
        "About": TransformationProfileType.REDUCE_ONLY,
        "Company Description": TransformationProfileType.REDUCE_ONLY,

        # Voice with strict constraints
        "Headline": TransformationProfileType.VOICE_CONSTRAINED,
        "Title": TransformationProfileType.VOICE_CONSTRAINED,
        "Subhead": TransformationProfileType.VOICE_CONSTRAINED,
        "Tagline": TransformationProfileType.VOICE_CONSTRAINED,

        # Voice with format preservation
        "Key Facts": TransformationProfileType.VOICE_FORMATTED,
        "Bullet Points": TransformationProfileType.VOICE_FORMATTED,
        "List": TransformationProfileType.VOICE_FORMATTED,
        "Features": TransformationProfileType.VOICE_FORMATTED,
        "Benefits": TransformationProfileType.VOICE_FORMATTED,

        # Full voice transformation
        "Lede": TransformationProfileType.VOICE_FULL,
        "Body": TransformationProfileType.VOICE_FULL,
        "Introduction": TransformationProfileType.VOICE_FULL,
        "Paragraph": TransformationProfileType.VOICE_FULL,
        "Conclusion": TransformationProfileType.VOICE_FULL,
        "Problem": TransformationProfileType.VOICE_FULL,
        "Solution": TransformationProfileType.VOICE_FULL,
        "Agitate": TransformationProfileType.VOICE_FULL,
    }

    @classmethod
    def get_profile_for_section(
        cls,
        section_name: str,
        story_model_override: Optional[str] = None,
        template_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transformation profile for a section with cascade logic.

        Cascade order:
        1. Template override (if provided)
        2. Story Model override (if provided)
        3. Section type default mapping
        4. Fallback to VOICE_FULL

        Args:
            section_name: Name of the section (e.g., "Headline", "Quote 1")
            story_model_override: Optional profile override from Story Model
            template_override: Optional profile override from Template

        Returns:
            Profile definition dict
        """
        # Cascade logic
        profile_type = None

        # 1. Template override (highest priority)
        if template_override:
            profile_type = TransformationProfileType(template_override)

        # 2. Story Model override
        elif story_model_override:
            profile_type = TransformationProfileType(story_model_override)

        # 3. Section type default mapping
        elif section_name in cls.SECTION_TYPE_MAPPINGS:
            profile_type = cls.SECTION_TYPE_MAPPINGS[section_name]

        # 4. Fallback
        else:
            profile_type = TransformationProfileType.VOICE_FULL

        return cls.PROFILES[profile_type]

    @classmethod
    def build_profile_prompt(
        cls,
        profile: Dict[str, Any],
        voice_config: Dict[str, Any],
        content: str,
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build transformation prompt for a specific profile.

        Args:
            profile: Transformation profile definition
            voice_config: Brand voice configuration (traits, tone, lexicon)
            content: Content to transform
            constraints: Optional section constraints (max_words, format, etc.)

        Returns:
            Complete prompt for LLM transformation
        """
        sections = []

        # Header - role and task
        sections.append("You are a professional copyeditor transforming content to match a specific brand voice.")
        sections.append("Apply the transformation instructions below while following the constraints.")
        sections.append("")

        # Profile Instructions
        sections.append("# Transformation Instructions")
        sections.append(profile["instructions"])
        sections.append("")

        # Add constraints if provided
        if constraints:
            sections.append("# Constraints")
            if "max_words" in constraints:
                sections.append(f"- Maximum words: {constraints['max_words']}")
            if "format" in constraints:
                sections.append(f"- Format: {constraints['format']}")
            if "required_elements" in constraints:
                sections.append(f"- Required elements: {', '.join(constraints['required_elements'])}")
            sections.append("")

        # Apply voice only if profile allows it
        if profile.get("apply_voice", False):
            sections.append("# Brand Voice")

            # Traits
            if "traits" in voice_config:
                traits = voice_config["traits"]
                if isinstance(traits, list):
                    sections.append(f"Traits: {', '.join(traits)}")
                elif isinstance(traits, str):
                    sections.append(f"Traits: {traits}")

            # Tone
            if "tone" in voice_config:
                tone = voice_config["tone"]
                if isinstance(tone, dict):
                    tone_desc = ", ".join([f"{k}: {v}" for k, v in tone.items()])
                    sections.append(f"Tone: {tone_desc}")
                elif isinstance(tone, str):
                    sections.append(f"Tone: {tone}")

            # Lexicon (word replacements)
            if "lexicon" in voice_config and voice_config["lexicon"]:
                sections.append("\n## Word Replacements")
                for old_word, new_word in voice_config["lexicon"].items():
                    sections.append(f"- Replace '{old_word}' with '{new_word}'")

            sections.append("")
        else:
            sections.append("# Brand Voice")
            sections.append("Do NOT apply brand voice to this content. Preserve original voice.")
            sections.append("")

        # Content to transform
        sections.append("# Content to Transform")
        sections.append(content)
        sections.append("")

        # JSON output format
        sections.append("# OUTPUT FORMAT")
        sections.append("Return your response as valid JSON with this exact structure:")
        sections.append("{")
        sections.append('  "transformed_content": "The transformed content here...",')
        sections.append('  "transformation_notes": "Brief explanation of key changes made (e.g., tone adjustments, word replacements, constraint handling, etc.)"')
        sections.append("}")
        sections.append("")
        sections.append("IMPORTANT: Return ONLY the JSON object, no additional text before or after.")

        return '\n'.join(sections)

    @classmethod
    def get_all_profiles(cls) -> Dict[str, Dict[str, Any]]:
        """Get all available transformation profiles"""
        return cls.PROFILES

    @classmethod
    def get_section_mappings(cls) -> Dict[str, str]:
        """Get all section type to profile mappings"""
        return {k: v.value for k, v in cls.SECTION_TYPE_MAPPINGS.items()}


# Example usage and testing
if __name__ == '__main__':
    profiles = TransformationProfiles()

    print("=" * 80)
    print("TRANSFORMATION PROFILES")
    print("=" * 80)

    # Show all profiles
    print("\n# Available Profiles:")
    for profile_type, profile_def in profiles.PROFILES.items():
        print(f"\n## {profile_type.value.upper()}")
        print(f"Name: {profile_def['name']}")
        print(f"Description: {profile_def['description']}")
        print(f"Apply Voice: {profile_def['apply_voice']}")

    # Show section mappings
    print("\n" + "=" * 80)
    print("SECTION TYPE MAPPINGS")
    print("=" * 80)

    for section_type, profile_type in profiles.SECTION_TYPE_MAPPINGS.items():
        print(f"{section_type:<25} → {profile_type.value}")

    # Test profile lookup
    print("\n" + "=" * 80)
    print("PROFILE LOOKUP TESTS")
    print("=" * 80)

    test_sections = ["Headline", "Quote 1", "Body", "Boilerplate", "Unknown Section"]

    for section in test_sections:
        profile = profiles.get_profile_for_section(section)
        print(f"\n{section}:")
        print(f"  Profile: {profile['name']}")
        print(f"  Apply Voice: {profile['apply_voice']}")

    # Test prompt building
    print("\n" + "=" * 80)
    print("PROMPT BUILDING TEST")
    print("=" * 80)

    test_voice_config = {
        "traits": ["Bold", "Direct", "Technical"],
        "tone": {"formality": "professional", "energy": "confident"},
        "lexicon": {
            "utilize": "use",
            "leverage": "use"
        }
    }

    test_content = "We utilize cutting-edge technology to leverage our platform."
    test_constraints = {"max_words": 10}

    headline_profile = profiles.get_profile_for_section("Headline")
    prompt = profiles.build_profile_prompt(
        headline_profile,
        test_voice_config,
        test_content,
        test_constraints
    )

    print("\nPrompt for Headline transformation:")
    print("-" * 80)
    print(prompt)
