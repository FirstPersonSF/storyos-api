"""
LLM-Based Voice Transformer Service

Uses Claude API to apply brand voice rules intelligently with context-awareness.
"""
from typing import Dict, List, Any, Optional
from services.llm_client import get_llm_client


class LLMVoiceTransformer:
    """Transform content using LLM with brand voice guidelines"""

    def __init__(self):
        self.llm_client = get_llm_client()

    def apply_voice(
        self,
        content: str,
        voice_config: Dict[str, Any],
        use_llm: bool = True
    ) -> str:
        """
        Apply voice transformation using LLM

        Args:
            content: Original content to transform
            voice_config: Complete BrandVoice configuration including:
                - traits: List[str]
                - tone_rules: Dict (formality, POV, etc.)
                - style_guardrails: Dict (do's, don'ts)
                - lexicon: Dict (required, banned, preferred terms)
                - rules: Dict (legacy transformation rules)
            use_llm: If False, skip LLM (for testing/comparison)

        Returns:
            Transformed content
        """
        if not use_llm:
            # Fallback: return original (could call old regex transformer)
            return content

        if not content or not content.strip():
            return content

        # Build comprehensive prompt from all voice guidelines
        prompt = self._build_transformation_prompt(voice_config, content)

        # Transform via LLM
        try:
            transformed = self.llm_client.transform_content(
                prompt=prompt,
                temperature=0.0  # Deterministic for consistency
            )
            return transformed.strip()
        except Exception as e:
            # On error, return original content with warning logged
            print(f"Voice transformation error: {e}")
            return content

    def _build_transformation_prompt(
        self,
        voice_config: Dict[str, Any],
        content: str
    ) -> str:
        """
        Build comprehensive transformation prompt from voice configuration

        Incorporates ALL brand voice guidelines:
        - Brand traits (personality)
        - Tone rules (formality, POV, sentence structure)
        - Style guardrails (do's and don'ts)
        - Lexicon (required/banned/preferred terms)
        - Transformation rules (lexicon mappings, terminology)
        """
        sections = []

        # Header
        sections.append(
            "You are a professional copyeditor transforming content to match a specific brand voice. "
            "Apply the brand voice guidelines below while preserving the meaning, structure, and formatting."
        )

        # Brand Traits
        traits = voice_config.get('traits', [])
        if traits:
            traits_str = ', '.join(traits)
            sections.append(f"\n## BRAND PERSONALITY\n{traits_str}")

        # Tone Rules
        tone_rules = voice_config.get('tone_rules', {})
        if tone_rules:
            tone_instructions = self._build_tone_instructions(tone_rules)
            if tone_instructions:
                sections.append(f"\n## TONE GUIDELINES\n{tone_instructions}")

        # Style Guardrails
        style_guardrails = voice_config.get('style_guardrails', {})
        if style_guardrails:
            style_instructions = self._build_style_instructions(style_guardrails)
            if style_instructions:
                sections.append(f"\n## STYLE GUARDRAILS\n{style_instructions}")

        # Lexicon (from new structure)
        lexicon = voice_config.get('lexicon', {})
        if lexicon:
            lexicon_instructions = self._build_lexicon_instructions(lexicon)
            if lexicon_instructions:
                sections.append(f"\n## TERMINOLOGY\n{lexicon_instructions}")

        # Transformation Rules (from legacy structure)
        rules = voice_config.get('rules', {})
        if rules:
            rules_instructions = self._build_rules_instructions(rules)
            if rules_instructions:
                sections.append(f"\n## WORD REPLACEMENTS\n{rules_instructions}")

        # Important reminders
        sections.append(
            "\n## IMPORTANT RULES\n"
            "- Only replace pronouns when they clearly refer to the company (not when part of other words)\n"
            "- Preserve all markdown formatting (bold, italics, line breaks, numbered lists, etc.)\n"
            "- Maintain the natural flow and readability\n"
            "- Do NOT add explanations, preambles, or meta-commentary\n"
            "- Return ONLY the transformed content"
        )

        # Content to transform
        sections.append(f"\n## CONTENT TO TRANSFORM\n\n{content}")

        sections.append("\n## TRANSFORMED CONTENT")

        return '\n'.join(sections)

    def _build_tone_instructions(self, tone_rules: Dict[str, Any]) -> str:
        """Convert tone_rules to instructions"""
        instructions = []

        formality = tone_rules.get('formality')
        if formality:
            if 'high' in formality.lower():
                instructions.append(f"- Formality: {formality} (expand contractions, use formal language)")
            elif 'low' in formality.lower() or 'casual' in formality.lower():
                instructions.append(f"- Formality: {formality} (use contractions, conversational tone)")
            else:
                instructions.append(f"- Formality: {formality}")

        pov = tone_rules.get('point_of_view')
        if pov:
            instructions.append(f"- Point of view: {pov}")

        sentence_length = tone_rules.get('sentence_length')
        if sentence_length:
            instructions.append(f"- Sentence length: {sentence_length}")

        voice = tone_rules.get('voice')
        if voice:
            instructions.append(f"- Voice: {voice}")

        contractions = tone_rules.get('contractions')
        if contractions:
            instructions.append(f"- Contractions: {contractions}")

        tense = tone_rules.get('tense')
        if tense:
            instructions.append(f"- Tense: {tense}")

        return '\n'.join(instructions)

    def _build_style_instructions(self, style_guardrails: Dict[str, Any]) -> str:
        """Convert style_guardrails to instructions"""
        instructions = []

        do_list = style_guardrails.get('do', [])
        if do_list:
            instructions.append("DO:")
            for item in do_list:
                instructions.append(f"  - {item}")

        dont_list = style_guardrails.get('dont', [])
        if dont_list:
            if instructions:  # Add spacing if we had DO items
                instructions.append("")
            instructions.append("DON'T:")
            for item in dont_list:
                instructions.append(f"  - {item}")

        punctuation = style_guardrails.get('punctuation')
        if punctuation:
            if instructions:
                instructions.append("")
            instructions.append(f"Punctuation: {punctuation}")

        return '\n'.join(instructions)

    def _build_lexicon_instructions(self, lexicon: Dict[str, Any]) -> str:
        """Convert lexicon to instructions"""
        instructions = []

        required = lexicon.get('required', [])
        if required:
            instructions.append("REQUIRED phrases to include when appropriate:")
            for term in required:
                instructions.append(f'  - "{term}"')

        banned = lexicon.get('banned', [])
        if banned:
            if instructions:
                instructions.append("")
            instructions.append("BANNED phrases to avoid:")
            for term in banned:
                instructions.append(f'  - "{term}"')

        preferred = lexicon.get('preferred', [])
        if preferred:
            if instructions:
                instructions.append("")
            instructions.append("PREFERRED terms:")
            for term in preferred:
                instructions.append(f'  - "{term}"')

        return '\n'.join(instructions)

    def _build_rules_instructions(self, rules: Dict[str, Any]) -> str:
        """Convert transformation rules to instructions"""
        instructions = []

        # Lexicon replacements (e.g., "the company" → "Hexagon AB")
        lexicon = rules.get('lexicon', {})
        if lexicon:
            for category, mapping in lexicon.items():
                generic_terms = mapping.get('generic', [])
                branded_term = mapping.get('branded', '')

                if generic_terms and branded_term:
                    terms_str = ', '.join([f'"{t}"' for t in generic_terms])
                    instructions.append(
                        f"- Replace {terms_str} with \"{branded_term}\" "
                        f"(only when referring to the company, not when part of other words)"
                    )

        # Terminology preferences
        terminology = rules.get('terminology', {})
        if terminology:
            preferred_terms = terminology.get('preferred_terms', {})
            if preferred_terms:
                if instructions:
                    instructions.append("")
                instructions.append("Preferred terminology:")
                for standard, preferred in preferred_terms.items():
                    instructions.append(f'  - Use "{preferred}" instead of "{standard}"')

        return '\n'.join(instructions)


# Create singleton instance
_transformer = None


def get_voice_transformer() -> LLMVoiceTransformer:
    """Get or create singleton voice transformer"""
    global _transformer
    if _transformer is None:
        _transformer = LLMVoiceTransformer()
    return _transformer
