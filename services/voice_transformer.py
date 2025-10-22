"""
Voice Transformer Service

Applies brand voice rules to transform content tone, style, and terminology.
"""
from typing import Dict, List, Any
import re


class VoiceTransformer:
    """Transform content according to brand voice rules"""

    def apply_voice(self, content: str, voice_rules: Dict[str, Any]) -> str:
        """
        Apply voice transformation pipeline

        Args:
            content: Original content to transform
            voice_rules: Voice rules from BrandVoice.rules

        Returns:
            Transformed content
        """
        if not voice_rules:
            return content

        # Step 1: Lexicon replacement (generic → brand-specific)
        content = self._apply_lexicon(content, voice_rules.get('lexicon', {}))

        # Step 2: Terminology alignment (industry terms → brand terms)
        content = self._apply_terminology(content, voice_rules.get('terminology', {}))

        # Step 3: Tone transformation (formality, perspective)
        content = self._apply_tone(content, voice_rules.get('tone_rules', []))

        return content

    def _apply_lexicon(self, content: str, lexicon: Dict[str, Any]) -> str:
        """
        Replace generic terms with brand-specific terms

        Example:
            lexicon = {
                "company_reference": {
                    "generic": ["the company", "the organization"],
                    "branded": "Hexagon"
                }
            }
        """
        if not lexicon:
            return content

        for category, mapping in lexicon.items():
            generic_terms = mapping.get('generic', [])
            branded_term = mapping.get('branded', '')

            if not branded_term:
                continue

            for generic in generic_terms:
                # Use word boundaries to avoid matching within other words
                # For multi-word phrases, use \b at start and end
                # For single words, use lookbehind/lookahead to avoid matching inside words
                escaped_generic = re.escape(generic)

                # Check if it's a single word or multi-word phrase
                if ' ' in generic:
                    # Multi-word phrase - use word boundaries
                    pattern = r'\b' + escaped_generic + r'\b'
                else:
                    # Single word - use lookbehind/lookahead for more precise matching
                    pattern = r'(?<![a-zA-Z])' + escaped_generic + r'(?![a-zA-Z])'

                content = re.sub(pattern, branded_term, content, flags=re.IGNORECASE)

        return content

    def _apply_terminology(self, content: str, terminology: Dict[str, Any]) -> str:
        """
        Replace industry-standard terms with brand-specific terminology

        Example:
            terminology = {
                "preferred_terms": {
                    "digital transformation": "digital reality solutions",
                    "automation": "autonomous technologies"
                }
            }
        """
        if not terminology:
            return content

        preferred_terms = terminology.get('preferred_terms', {})

        for standard_term, brand_term in preferred_terms.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(standard_term), re.IGNORECASE)
            content = pattern.sub(brand_term, content)

        return content

    def _apply_tone(self, content: str, tone_rules: List[Dict[str, Any]]) -> str:
        """
        Apply tone transformations (formality, perspective)

        This is a simplified implementation. Full implementation would use:
        - NLP for sentence detection
        - Grammar parsing for perspective shifts
        - LLM integration for sophisticated transformations

        For Phase 2, we'll focus on simple pattern-based replacements.
        """
        if not tone_rules:
            return content

        for rule in tone_rules:
            rule_type = rule.get('type')

            if rule_type == 'formality':
                content = self._apply_formality(content, rule)
            elif rule_type == 'perspective':
                content = self._apply_perspective(content, rule)

        return content

    def _apply_formality(self, content: str, rule: Dict[str, Any]) -> str:
        """
        Adjust formality level

        Example rule:
            {
                "type": "formality",
                "level": "formal",
                "patterns": {
                    "We're": "We are",
                    "don't": "do not"
                }
            }
        """
        level = rule.get('level', 'neutral')
        patterns = rule.get('patterns', {})

        if level == 'formal':
            # Expand contractions
            contractions = {
                "We're": "We are",
                "we're": "we are",
                "don't": "do not",
                "doesn't": "does not",
                "can't": "cannot",
                "won't": "will not",
                "it's": "it is",
                "that's": "that is",
                "what's": "what is"
            }
            # Merge with custom patterns
            contractions.update(patterns)

            for contraction, expansion in contractions.items():
                content = content.replace(contraction, expansion)

        elif level == 'casual':
            # Use contractions (reverse of formal)
            expansions = {
                "We are": "We're",
                "we are": "we're",
                "do not": "don't",
                "does not": "doesn't",
                "cannot": "can't",
                "will not": "won't",
                "it is": "it's",
                "that is": "that's"
            }
            # Merge with custom patterns
            expansions.update(patterns)

            for expansion, contraction in expansions.items():
                # Use word boundaries to avoid partial matches
                pattern = r'\b' + re.escape(expansion) + r'\b'
                content = re.sub(pattern, contraction, content)

        return content

    def _apply_perspective(self, content: str, rule: Dict[str, Any]) -> str:
        """
        Shift perspective (first-person ↔ third-person)

        Example rule:
            {
                "type": "perspective",
                "value": "third_person",
                "company_name": "Hexagon"
            }
        """
        perspective = rule.get('value', 'third_person')
        company_name = rule.get('company_name', 'the company')

        if perspective == 'third_person':
            # First person → Third person
            # Use lookbehind and lookahead to ensure we're matching whole words,
            # not substrings within other words
            replacements = {
                r'(?<![a-zA-Z])We(?![a-zA-Z])': company_name,
                r'(?<![a-zA-Z])we(?![a-zA-Z])': company_name,
                r'(?<![a-zA-Z])Our(?![a-zA-Z])': f"{company_name}'s",
                r'(?<![a-zA-Z])our(?![a-zA-Z])': f"{company_name}'s",
                r'(?<![a-zA-Z])Us(?![a-zA-Z])': company_name,
                r'(?<![a-zA-Z])us(?![a-zA-Z])': company_name
            }

            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)

        elif perspective == 'first_person':
            # Third person → First person
            # This requires company_name to be specified
            if company_name and company_name != 'the company':
                replacements = {
                    company_name: 'we',
                    f"{company_name}'s": 'our'
                }

                for term, replacement in replacements.items():
                    pattern = r'\b' + re.escape(term) + r'\b'
                    content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

        return content


# Example usage and testing
if __name__ == '__main__':
    transformer = VoiceTransformer()

    # Test content
    test_content = """
The company announces the launch of its next-generation measurement platform.
We're excited to bring digital transformation to manufacturers worldwide.
This automation solution enables precision manufacturing.
"""

    # Corporate voice rules (formal, third-person)
    corporate_rules = {
        "lexicon": {
            "company_reference": {
                "generic": ["the company", "the organization"],
                "branded": "Hexagon AB"
            }
        },
        "terminology": {
            "preferred_terms": {
                "digital transformation": "digital reality solutions",
                "automation": "autonomous technologies"
            }
        },
        "tone_rules": [
            {
                "type": "formality",
                "level": "formal"
            },
            {
                "type": "perspective",
                "value": "third_person",
                "company_name": "Hexagon AB"
            }
        ]
    }

    # Product voice rules (casual, first-person)
    product_rules = {
        "lexicon": {
            "company_reference": {
                "generic": ["the company", "the organization"],
                "branded": "we"
            }
        },
        "terminology": {
            "preferred_terms": {
                "digital transformation": "smart digital tools",
                "automation": "smart automation"
            }
        },
        "tone_rules": [
            {
                "type": "formality",
                "level": "casual"
            },
            {
                "type": "perspective",
                "value": "first_person"
            }
        ]
    }

    print("ORIGINAL:")
    print(test_content)

    print("\n" + "=" * 80)
    print("CORPORATE VOICE (formal, third-person):")
    print(transformer.apply_voice(test_content, corporate_rules))

    print("\n" + "=" * 80)
    print("PRODUCT VOICE (casual, first-person):")
    print(transformer.apply_voice(test_content, product_rules))
