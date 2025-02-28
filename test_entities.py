from allyanonimiser import create_allyanonimiser

ally = create_allyanonimiser()
entity_types = ally.get_available_entity_types()

print('Available entity types:')
for entity_type, metadata in entity_types.items():
    print(f'- {entity_type}: {metadata["description"]} (Example: {metadata["example"]})')
