from PyPDF2 import PdfReader
import re

pdf = PdfReader('/Users/mcfatem/GitHub/generate-metadata-using-Copilot/2023_Bethany_Chinedu_Willig-Onwuachi.pdf')
text = pdf.pages[0].extract_text()
text_clean = ' '.join(text.split())

# Get first paragraph of introduction
intro_match = re.search(r'Intr?oduction\s+(.*?)(?:As I have|Recently)', text_clean, re.IGNORECASE)
if intro_match:
    intro = intro_match.group(1).strip()
    sentences = re.split(r'(?<=[.!?])\s+', intro)
    print(f'Sentences found: {len(sentences)}')
    print(f'\nFirst 3 sentences:\n{" ".join(sentences[:3])}')
else:
    print("No intro match found")
