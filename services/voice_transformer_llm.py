"""
LLM-Based Voice Transformer Service

Uses Claude API to apply brand voice rules intelligently with context-awareness.
Supports transformation profiles for section-aware transformation strategies.
"""
from typing import Dict, List, Any, Optional
import re
from services.llm_client import get_llm_client
from services.transformation_profiles import TransformationProfiles


class LLMVoiceTransformer:
    """Transform content using LLM with brand voice guidelines"""

    def __init__(self):
        self.llm_client = get_llm_client()

    def _extract_meta_commentary(self, content: str) -> tuple[str, str]:
        """
        Extract meta-commentary from LLM response, separating it from the actual content.

        Returns:
            tuple: (cleaned_content, commentary)
                - cleaned_content: The transformed content without meta-commentary
                - commentary: The extracted meta-commentary for reference
        """
        lines = content.split('\n')
        content_lines = []
        commentary_lines = []
        skip_mode = False
        commentary_started = False

        for line in lines:
            line_lower = line.lower().strip()

            # Detect meta-commentary headers
            if any(phrase in line_lower for phrase in [
                "here's the transformed content",
                "transformed content:",
                "key transformation notes",
                "key adjustments:",
                "key adjustments made",
                "key observations:",
                "note:",
                "notes on transformation:",
                "the transformation maintains",
                "the transformation emphasizes",
                "the transformation elevates",
                "the transformed text",
                "updated version:",
                "strategic release",
                "this transformation",
                "aligned with the specified brand voice"
            ]):
                skip_mode = True
                commentary_started = True
                commentary_lines.append(line)
                continue

            # If we see a bullet/dash at start after meta-commentary header, it's commentary
            if skip_mode and (line_lower.startswith('*') or line_lower.startswith('-') or line_lower.startswith('•')):
                commentary_lines.append(line)
                continue

            # Exit skip mode if we see substantial content again
            if skip_mode and len(line.strip()) > 50 and not commentary_started:
                skip_mode = False

            if skip_mode or commentary_started:
                commentary_lines.append(line)
            else:
                content_lines.append(line)

        cleaned_content = '\n'.join(content_lines).strip()

        # Also check for commentary at the end (common pattern)
        paragraphs = cleaned_content.split('\n\n')
        while paragraphs and len(paragraphs) > 1:
            last_para = paragraphs[-1].lower()
            if any(phrase in last_para for phrase in [
                'note:',
                'notes on transformation',
                'the transformation',
                'the transformed text',
                'key adjustments',
                'key adjustments made',
                'key observations',
                'this maintains',
                'this elevates',
                'aligned with the specified brand voice',
                'incorporated brand voice',
                'maintained',
                'preserved',
                'used more'
            ]):
                commentary_lines.append(paragraphs.pop())
            else:
                break

        cleaned_content = '\n\n'.join(paragraphs).strip()
        commentary = '\n'.join(commentary_lines).strip()

        return cleaned_content, commentary

    def apply_voice(
        self,
        content: str,
        voice_config: Dict[str, Any],
        use_llm: bool = True
    ) -> tuple[str, str]:
        """
        Apply voice transformation using LLM (legacy method)

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
            tuple: (transformed_content, transformation_notes)
        """
        if not use_llm:
            # Fallback: return original (could call old regex transformer)
            return content, ""

        if not content or not content.strip():
            return content, ""

        # Build comprehensive prompt from all voice guidelines
        prompt = self._build_transformation_prompt(voice_config, content)

        # Transform via LLM
        try:
            transformed = self.llm_client.transform_content(
                prompt=prompt,
                temperature=0.0  # Deterministic for consistency
            )

            # Parse JSON response
            import json
            import os
            import time

            # DEBUG: Save raw response to file for inspection
            debug_dir = '/Users/drewf/Desktop/Python/storyos_protoype/llm_debug'
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = f"{debug_dir}/response_{int(time.time() * 1000)}.json"
            with open(debug_file, 'w') as f:
                f.write(f"=== RAW RESPONSE ===\n{transformed}\n\n")

            # Clean up response (remove markdown code blocks if present)
            json_str = transformed.strip()

            # Remove markdown code blocks
            if json_str.startswith('```'):
                # Find end of first line (```json or just ```)
                first_newline = json_str.find('\n')
                if first_newline != -1:
                    json_str = json_str[first_newline+1:]
                # Remove closing ```
                if json_str.endswith('```'):
                    json_str = json_str[:json_str.rfind('```')]

            json_str = json_str.strip()

            # DEBUG: Save cleaned JSON string
            with open(debug_file, 'a') as f:
                f.write(f"=== CLEANED JSON ===\n{json_str}\n\n")

            # Try parsing
            try:
                result = json.loads(json_str, strict=False)
                if isinstance(result, dict) and 'transformed_content' in result:
                    with open(debug_file, 'a') as f:
                        f.write(f"=== PARSED SUCCESSFULLY ===\n")
                    return result.get('transformed_content', '').strip(), result.get('transformation_notes', '')
            except json.JSONDecodeError as json_err:
                print(f"JSON parsing error: {json_err}")
                print(f"Attempted to parse: {json_str[:200]}...")
                print(f"Full response saved to: {debug_file}")
                with open(debug_file, 'a') as f:
                    f.write(f"=== PARSE ERROR ===\n{json_err}\n")

            # Final fallback: return original content
            print("Could not parse JSON, returning original content")
            print(f"Full response saved to: {debug_file}")
            return content, "JSON parsing failed"

        except Exception as e:
            # On error, return original content with warning logged
            print(f"Voice transformation error: {e}")
            return content, ""

    def apply_voice_with_profile(
        self,
        content: str,
        voice_config: Dict[str, Any],
        section_name: str,
        constraints: Optional[Dict[str, Any]] = None,
        story_model_override: Optional[str] = None,
        template_override: Optional[str] = None,
        use_llm: bool = True
    ) -> tuple[str, str]:
        """
        Apply voice transformation using section-aware transformation profile.

        This is the preferred method for deliverable rendering as it respects
        section-specific transformation strategies.

        Args:
            content: Original content to transform
            voice_config: Brand voice configuration
            section_name: Name of section (e.g., "Headline", "Quote 1", "Body")
            constraints: Optional section constraints (max_words, format, etc.)
            story_model_override: Optional profile override from Story Model
            template_override: Optional profile override from Template
            use_llm: If False, skip LLM (for testing/comparison)

        Returns:
            tuple: (transformed_content, transformation_notes)
        """
        if not use_llm:
            return content, ""

        if not content or not content.strip():
            return content, ""

        # Get transformation profile for this section
        profile = TransformationProfiles.get_profile_for_section(
            section_name=section_name,
            story_model_override=story_model_override,
            template_override=template_override
        )

        # If profile says don't apply voice, return content as-is
        if not profile.get('apply_voice', False):
            # For PRESERVE profile, return exactly as provided
            # For REDUCE_ONLY profile, check if content exceeds constraints
            if constraints and 'max_words' in constraints:
                word_count = len(content.split())
                max_words = constraints['max_words']
                if word_count > max_words:
                    # Only reduce if necessary
                    prompt = TransformationProfiles.build_profile_prompt(
                        profile=profile,
                        voice_config=voice_config,
                        content=content,
                        constraints=constraints
                    )
                    try:
                        transformed = self.llm_client.transform_content(
                            prompt=prompt,
                            temperature=0.0
                        )
                        cleaned, commentary = self._extract_meta_commentary(transformed)
                        return cleaned.strip(), commentary
                    except Exception as e:
                        print(f"Voice transformation error: {e}")
                        return content, ""
            return content, ""

        # Build profile-specific prompt
        prompt = TransformationProfiles.build_profile_prompt(
            profile=profile,
            voice_config=voice_config,
            content=content,
            constraints=constraints
        )

        # Transform via LLM
        try:
            transformed = self.llm_client.transform_content(
                prompt=prompt,
                temperature=0.0  # Deterministic for consistency
            )

            # Parse JSON response
            import json
            import os
            import time

            # DEBUG: Save raw response to file for inspection
            debug_dir = '/Users/drewf/Desktop/Python/storyos_protoype/llm_debug'
            os.makedirs(debug_dir, exist_ok=True)
            debug_file = f"{debug_dir}/response_{int(time.time() * 1000)}.json"
            with open(debug_file, 'w') as f:
                f.write(f"=== RAW RESPONSE ===\n{transformed}\n\n")

            # Clean up response (remove markdown code blocks if present)
            json_str = transformed.strip()

            # Remove markdown code blocks
            if json_str.startswith('```'):
                # Find end of first line (```json or just ```)
                first_newline = json_str.find('\n')
                if first_newline != -1:
                    json_str = json_str[first_newline+1:]
                # Remove closing ```
                if json_str.endswith('```'):
                    json_str = json_str[:json_str.rfind('```')]

            json_str = json_str.strip()

            # DEBUG: Save cleaned JSON string
            with open(debug_file, 'a') as f:
                f.write(f"=== CLEANED JSON ===\n{json_str}\n\n")

            # Try parsing
            try:
                result = json.loads(json_str, strict=False)
                if isinstance(result, dict) and 'transformed_content' in result:
                    with open(debug_file, 'a') as f:
                        f.write(f"=== PARSED SUCCESSFULLY ===\n")
                    return result.get('transformed_content', '').strip(), result.get('transformation_notes', '')
            except json.JSONDecodeError as json_err:
                print(f"JSON parsing error: {json_err}")
                print(f"Attempted to parse: {json_str[:200]}...")
                print(f"Full response saved to: {debug_file}")
                with open(debug_file, 'a') as f:
                    f.write(f"=== PARSE ERROR ===\n{json_err}\n")

            # Final fallback: return original content
            print("Could not parse JSON, returning original content")
            print(f"Full response saved to: {debug_file}")
            return content, "JSON parsing failed"

        except Exception as e:
            # On error, return original content with warning logged
            print(f"Voice transformation error: {e}")
            return content, ""

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
            "- Maintain the natural flow and readability"
        )

        # Content to transform
        sections.append(f"\n## CONTENT TO TRANSFORM\n\n{content}")

        # JSON output format
        sections.append(
            "\n## OUTPUT FORMAT\n"
            "Return your response as valid JSON with this exact structure:\n"
            "{\n"
            '  "transformed_content": "The transformed content here...",\n'
            '  "transformation_notes": "Brief explanation of key changes made (e.g., tone adjustments, word replacements, etc.)"\n'
            "}\n\n"
            "IMPORTANT: Return ONLY the JSON object, no additional text before or after."
        )

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
