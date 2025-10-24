#!/usr/bin/env python3
"""Test quote extraction from Principles list"""
import re

# Sample Principles content from the database
principles_content = """1. **Empowering** – We unlock human potential through technology and data.
2. **Entrepreneurial** – We act with curiosity, speed, and ownership to make progress.
3. **Real** – We stay grounded, practical, and focused on creating measurable impact.
4. **Responsible** – We make decisions that are good for people, profit, and the planet.
5. **Innovative** – We continuously improve how technology serves humanity."""

print("Testing quote extraction from Principles...")
print("=" * 80)
print("\nOriginal content:")
print(principles_content)
print("\n" + "=" * 80)

# Test the regex pattern
list_items = re.findall(r'^\d+\.\s+\*\*([^*]+)\*\*\s+[–—-]\s+(.+)$', principles_content, re.MULTILINE)

print(f"\nFound {len(list_items)} principles")

for i, (label, content) in enumerate(list_items, 1):
    print(f"\nPrinciple {i}:")
    print(f"  Label: {label}")
    print(f"  Content: {content}")

# Test Quote 1 extraction (should get first principle)
quote_num = 1
item_index = (quote_num - 1) % len(list_items)
item_label, item_content = list_items[item_index]
quote_1 = item_content.strip()

print("\n" + "=" * 80)
print(f"Quote 1 (extracted principle {quote_num}):")
print(f'"{quote_1}"')
print("— Burkhardt Boekem, Chief Technology Officer")

# Test Quote 2 extraction (should get second principle)
quote_num = 2
item_index = (quote_num - 1) % len(list_items)
item_label, item_content = list_items[item_index]
quote_2 = item_content.strip()

print("\n" + "=" * 80)
print(f"Quote 2 (extracted principle {quote_num}):")
print(f'"{quote_2}"')
print("— Customer Name, Customer Title")
