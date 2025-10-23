"""
Story Model Composer Service

Extracts and composes content according to story model section strategies.
"""
from typing import Dict, List, Any, Optional
from models.unf import Element as UNFElement


class StoryModelComposer:
    """Compose content according to story model structure"""

    def compose_section(
        self,
        section_name: str,
        section_strategy: Dict[str, Any],
        bound_elements: List[UNFElement],
        instance_data: Dict[str, Any]
    ) -> str:
        """
        Compose section content using story model strategy

        Args:
            section_name: Name of the section (e.g., "Headline", "Lede")
            section_strategy: Strategy definition from story model
            bound_elements: UNF elements bound to this section
            instance_data: Instance-specific data (who, what, when, etc.)

        Returns:
            Composed section content
        """
        if not bound_elements:
            return ""

        # Get extraction strategy
        strategy = section_strategy.get('extraction_strategy', 'full_content')

        # Apply strategy
        if strategy == 'key_message':
            content = self._extract_key_message(bound_elements, section_strategy)
        elif strategy == 'five_ws':
            content = self._extract_five_ws(bound_elements, instance_data)
        elif strategy == 'structured_list':
            content = self._extract_structured_list(bound_elements, section_strategy)
        elif strategy == 'quote':
            content = self._extract_quote(bound_elements, instance_data, section_strategy)
        elif strategy == 'full_content':
            content = self._extract_full_content(bound_elements, instance_data)
        else:
            # Default: concatenate all elements
            content = self._extract_full_content(bound_elements, instance_data)

        return content

    def _extract_key_message(
        self,
        elements: List[UNFElement],
        strategy: Dict[str, Any]
    ) -> str:
        """
        Extract key message for headlines

        Strategy: Use first sentence, truncate to max_words
        """
        if not elements:
            return ""

        # Use first element's content
        full_content = elements[0].content or ""

        # Get first sentence
        sentences = full_content.split('.')
        headline = sentences[0].strip()

        # Apply word limit
        max_words = strategy.get('max_words', 10)
        words = headline.split()

        if len(words) > max_words:
            headline = ' '.join(words[:max_words])

        return headline

    def _extract_five_ws(
        self,
        elements: List[UNFElement],
        instance_data: Dict[str, Any]
    ) -> str:
        """
        Compose lede using five W's (who, what, when, where, why)

        Uses instance data to construct lede sentence following
        journalistic inverted pyramid structure.
        """
        # Get element content (may contain placeholders)
        element_content = elements[0].content if elements else ""

        # If element has template, use it
        if '{who}' in element_content or '{what}' in element_content:
            # Element uses placeholders, inject instance data
            lede = element_content
            for field_name, field_value in instance_data.items():
                placeholder = f"{{{field_name}}}"
                lede = lede.replace(placeholder, str(field_value))
            return lede

        # Otherwise, construct standard lede format
        who = instance_data.get('who', 'The company')
        what = instance_data.get('what', 'announces news')
        when = instance_data.get('when', 'today')
        where = instance_data.get('where', '')
        why = instance_data.get('why', '')

        # Standard lede format: WHERE, WHEN — WHO WHAT. WHY.
        lede_parts = []

        if where and when:
            lede_parts.append(f"{where}, {when} — {who} {what}")
        elif when:
            lede_parts.append(f"{when} — {who} {what}")
        else:
            lede_parts.append(f"{who} {what}")

        if why:
            lede_parts.append(f" {why}")

        return '.'.join(lede_parts) + '.' if lede_parts else element_content

    def _extract_structured_list(
        self,
        elements: List[UNFElement],
        strategy: Dict[str, Any]
    ) -> str:
        """
        Extract structured list (e.g., key facts, bullet points)

        Strategy: Extract main points from element content
        """
        if not elements:
            return ""

        # Simple implementation: split on newlines or sentences
        points = []
        for element in elements:
            content = element.content or ""

            # Split on double newlines (paragraphs)
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if para and len(para) > 10:  # Skip very short fragments
                    points.append(para)

        # Format as list
        list_format = strategy.get('format', 'paragraph')

        if list_format == 'bullets':
            return '\n'.join([f"• {point}" for point in points])
        elif list_format == 'numbered':
            return '\n'.join([f"{i+1}. {point}" for i, point in enumerate(points)])
        else:
            # Paragraph format (default)
            return '\n\n'.join(points)

    def _extract_quote(
        self,
        elements: List[UNFElement],
        instance_data: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> str:
        """
        Extract quote with attribution

        Prefers quote content from instance data (quote1_content, quote2_content).
        Falls back to extracting from bound elements if no instance data provided.
        """
        # Get quote number from strategy
        quote_num = strategy.get('quote_number', 1)

        # Get speaker and title from instance data
        speaker_key = f"quote{quote_num}_speaker"
        title_key = f"quote{quote_num}_title"
        content_key = f"quote{quote_num}_content"

        speaker = instance_data.get(speaker_key, '')
        title = instance_data.get(title_key, '')

        # PREFER: Use quote content from instance data if provided
        quote_content = instance_data.get(content_key, '')

        # FALLBACK: Extract from elements if no instance data provided
        if not quote_content and elements:
            quote_content = elements[0].content or ""

            # Remove placeholder markers if present
            quote_content = quote_content.replace('{quote}', '').strip()

            # Detect if content is a numbered list (e.g., "1. Item\n2. Item")
            import re
            list_items = re.findall(r'^\d+\.\s+\*\*([^*]+)\*\*\s+[–—-]\s+(.+)$', quote_content, re.MULTILINE)

            if list_items:
                # Extract based on quote number (default to first item)
                item_index = (quote_num - 1) % len(list_items)  # Wrap around if quote_num exceeds list length
                item_label, item_content = list_items[item_index]
                quote_content = item_content.strip()
            else:
                # Check for simpler numbered list format
                simple_list = re.findall(r'^\d+\.\s+(.+)$', quote_content, re.MULTILINE)
                if simple_list and len(simple_list) > 1:
                    # Multiple items found, extract one
                    item_index = (quote_num - 1) % len(simple_list)
                    quote_content = simple_list[item_index].strip()
                    # Remove markdown bold markers if present
                    quote_content = re.sub(r'\*\*([^*]+)\*\*\s+[–—-]\s+', '', quote_content)

        # Format quote with attribution
        if speaker and title:
            return f'"{quote_content}"\n— {speaker}, {title}'
        elif speaker:
            return f'"{quote_content}"\n— {speaker}'
        else:
            return f'"{quote_content}"'

    def _extract_full_content(self, elements: List[UNFElement], instance_data: Dict[str, Any] = None) -> str:
        """
        Use complete element content

        Strategy: Concatenate all elements with double newlines,
        inject instance field placeholders if present
        """
        content_parts = []

        for element in elements:
            if element and element.content:
                content = element.content

                # Inject instance field placeholders if present
                if instance_data and ('{who}' in content or '{what}' in content or '{when}' in content or
                                      '{where}' in content or '{why}' in content or '{quote' in content):
                    for field_name, field_value in instance_data.items():
                        placeholder = f"{{{field_name}}}"
                        if placeholder in content:
                            content = content.replace(placeholder, str(field_value))

                content_parts.append(content)

        return '\n\n'.join(content_parts)


# Example usage and testing
if __name__ == '__main__':
    from models.unf import Element as UNFElement
    from uuid import uuid4
    from datetime import datetime

    composer = StoryModelComposer()

    # Test element
    test_element = UNFElement(
        id=uuid4(),
        layer='Foundational',
        name='Vision Statement',
        content='{where}, {when} — {who} {what}. {why}',
        status='approved',
        version='1.0',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Test instance data
    instance_data = {
        'who': 'Hexagon AB',
        'what': 'announces the launch of HxGN Precision One',
        'when': '2025-10-20',
        'where': 'Stockholm, Sweden',
        'why': 'To help manufacturers increase precision and reduce waste'
    }

    # Test Headline extraction
    print("=" * 80)
    print("HEADLINE EXTRACTION (key_message):")
    headline_strategy = {
        'extraction_strategy': 'key_message',
        'max_words': 8
    }

    key_message_element = UNFElement(
        id=uuid4(),
        layer='Foundational',
        name='Key Messages',
        content='Hexagon AB announces HxGN Precision One for manufacturing precision. This revolutionary platform increases accuracy by 40%.',
        status='approved',
        version='1.0',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    headline = composer.compose_section(
        section_name='Headline',
        section_strategy=headline_strategy,
        bound_elements=[key_message_element],
        instance_data=instance_data
    )
    print(headline)

    # Test Lede extraction
    print("\n" + "=" * 80)
    print("LEDE EXTRACTION (five_ws):")
    lede_strategy = {
        'extraction_strategy': 'five_ws'
    }

    lede = composer.compose_section(
        section_name='Lede',
        section_strategy=lede_strategy,
        bound_elements=[test_element],
        instance_data=instance_data
    )
    print(lede)

    # Test Full Content
    print("\n" + "=" * 80)
    print("BODY EXTRACTION (full_content):")
    body_strategy = {
        'extraction_strategy': 'full_content'
    }

    body_element = UNFElement(
        id=uuid4(),
        layer='Foundational',
        name='Product Description',
        content='HxGN Precision One is a next-generation measurement platform.\n\nIt combines sensor technology with advanced analytics.\n\nManufacturers can achieve 40% greater precision.',
        status='approved',
        version='1.0',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    body = composer.compose_section(
        section_name='Body',
        section_strategy=body_strategy,
        bound_elements=[body_element],
        instance_data=instance_data
    )
    print(body)
