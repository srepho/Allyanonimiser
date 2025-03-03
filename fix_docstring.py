import re

# Read the file
with open('allyanonimiser/allyanonimiser.py', 'r') as f:
    content = f.read()

# Find the problematic docstring and fix it
pattern = r'(?s)text = """\s+Customer: John Smith.*?"""'
replacement = '''text = "Customer: John Smith (DOB: 15/6/1980)\\nPolicy #: POL-12345678\\nEmail: john.smith@example.com\\nPhone: 0412-345-678\\n\\nCustomer reported an accident on 10/5/2024."'''

fixed_content = re.sub(pattern, replacement, content)

# Write the fixed content back
with open('allyanonimiser/allyanonimiser.py', 'w') as f:
    f.write(fixed_content)

print("Docstring fixed\!")
