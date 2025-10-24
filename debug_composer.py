"""Debug script to test story model composer output"""
import sys
sys.path.append('.')

from services.story_model_composer import StoryModelComposer
from models.unf import Element as UNFElement
from uuid import UUID, uuid4
from datetime import datetime

composer = StoryModelComposer()

# Vision Statement element (with placeholders)
vision_element = UNFElement(
    id=UUID('9425e539-b1dd-449b-af7b-b6f58c87334f'),
    layer_id=uuid4(),  # Generate proper UUID4
    name='Vision Statement',
    content='{where}, {when} — {who} {what}.\n\n{why}\n\nVision: A world where business, humanity, and the planet thrive together.',
    status='approved',
    version='1.3',
    created_at=datetime.now(),
    updated_at=datetime.now()
)

# Key Messages element
key_messages_element = UNFElement(
    id=UUID('9961a9a1-3b01-4c45-a6e4-422d18917d2d'),
    layer_id=uuid4(),  # Generate proper UUID4
    name='Key Messages',
    content='Key Message 1\n**Headline**: Transform data into real-world outcomes\n**Proof**: Our Reality Technology connects physical and digital realities to improve decision-making and productivity.',
    status='approved',
    version='1.3',
    created_at=datetime.now(),
    updated_at=datetime.now()
)

# Instance data from test
instance_data = {
    "who": "Hexagon AB",
    "what": "announces breakthrough in manufacturing intelligence platform",
    "when": "January 15, 2024",
    "where": "Stockholm, Sweden",
    "why": "to help manufacturers increase precision and reduce waste",
    "quote1_speaker": "Paolo Guglielmini",
    "quote1_title": "President, Hexagon Manufacturing Intelligence",
    "quote1_content": "This breakthrough represents a fundamental shift in how manufacturers approach precision and efficiency."
}

# Test Lede composition (five_ws strategy)
print("="*80)
print("TESTING LEDE (five_ws strategy)")
print("="*80)
lede_strategy = {'extraction_strategy': 'five_ws'}
lede_output = composer.compose_section(
    section_name='Lede',
    section_strategy=lede_strategy,
    bound_elements=[vision_element],
    instance_data=instance_data
)
print(f"Output length: {len(lede_output)} chars")
print(f"Output:\n{lede_output}")

# Test Headline composition (key_message strategy)
print("\n" + "="*80)
print("TESTING HEADLINE (key_message strategy)")
print("="*80)
headline_strategy = {'extraction_strategy': 'key_message', 'max_words': 10}
headline_output = composer.compose_section(
    section_name='Headline',
    section_strategy=headline_strategy,
    bound_elements=[key_messages_element],
    instance_data=instance_data
)
print(f"Output length: {len(headline_output)} chars")
print(f"Output:\n{headline_output}")
