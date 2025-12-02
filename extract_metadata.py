#!/usr/bin/env python3
"""
Extract metadata from PDFs and generate Dublin Core metadata CSV
"""

import os
import csv
import re
from PyPDF2 import PdfReader
from pathlib import Path

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return ""

def extract_year_from_filename(filename):
    """Extract year from filename like '2001_Melissa_Yates.pdf' or '2004 Elizabeth A. Allan.pdf'"""
    match = re.match(r'(\d{4})[\s_]', filename)
    return match.group(1) if match else ""

def extract_author_from_filename(filename):
    """Extract author name from filename and format as 'Last, First'"""
    # Remove year prefix and .pdf extension
    name_part = re.sub(r'^\d{4}[\s_]+', '', filename)
    name_part = re.sub(r'\.pdf$', '', name_part)
    # Replace underscores with spaces
    name_part = name_part.replace('_', ' ')
    
    # Parse the name to convert to "Last, First" format
    # Handle cases like "Elizabeth A. Allan" or "Joe Wlos" or "Bethany Chinedu Willig-Onwuachi"
    parts = name_part.split()
    
    if len(parts) >= 2:
        # Check if last part is a hyphenated last name or simple last name
        last_name = parts[-1]
        first_parts = parts[:-1]
        
        # Format as "Last, First Middle"
        formatted_name = f"{last_name}, {' '.join(first_parts)}"
        return formatted_name
    else:
        # Fallback if parsing fails
        return name_part

def analyze_pdf_content(pdf_path, text):
    """Analyze PDF content and generate metadata"""
    filename = os.path.basename(pdf_path)
    year = extract_year_from_filename(filename)
    author = extract_author_from_filename(filename)
    
    # Try to get metadata from PDF
    try:
        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)
        pdf_metadata = reader.metadata
    except:
        page_count = 0
        pdf_metadata = None
    
    # Initialize title
    title = ""
    
    # Try to extract title from text if available
    if text and len(text.strip()) > 20:
        # Check for title between pipes (e.g., "Author | Title | Page")
        pipe_match = re.search(r'\|\s*([^|]{10,100})\s*\|', text[:200])
        if pipe_match:
            potential_title = pipe_match.group(1).strip()
            # Make sure it's not a page number or author name
            if not potential_title.isdigit() and potential_title.lower() not in author.lower():
                title = potential_title
        
        # Check for title in quotes if no pipe title found
        if not title:
            quote_match = re.search(r'"([^"]{10,100})"', text[:1000])
            if quote_match:
                potential_title = quote_match.group(1)
                # Make sure it's not just a quote from the abstract
                if 'abstract' not in potential_title.lower():
                    title = potential_title
        
        # If no quoted title found, try line-based extraction
        if not title:
            # Split into lines for better analysis
            lines = text.split('\n')
            
            # Look for title - it usually appears after author name/page number and before "By:" or "Introduction"
            title_lines = []
            started = False
            
            for i, line in enumerate(lines):
                line_strip = line.strip()
                
                # Skip empty lines and very short lines at the start
                if not started and (not line_strip or len(line_strip) < 4 or line_strip.isdigit()):
                    continue
                
                # Skip author name fragments at the beginning
                if not started and any(name.lower() in line_strip.lower() for name in author.split()[:2]):
                    continue
                
                # Start collecting when we hit a substantive line
                if not started and len(line_strip) >= 4:
                    started = True
                
                # Stop at markers
                if line_strip.lower() in ['by:', 'introduction', 'abstract', 'intr oduction'] or line_strip.lower().startswith('by:'):
                    break
                
                # Collect title lines
                if started and line_strip and not line_strip.isdigit():
                    title_lines.append(line_strip)
                    # Safety limit
                    if len(' '.join(title_lines)) > 250:
                        break
            
            if title_lines:
                # Join and clean
                potential_title = ' '.join(title_lines)
                # Remove "By:" suffix if present
                potential_title = re.sub(r'\s*By:\s*$', '', potential_title, flags=re.IGNORECASE)
                # Remove fragments of author's last name at the start
                words = potential_title.split()
                if len(words) > 3:
                    # Check if first two words form author's last name (e.g., "W illig" -> "Willig")
                    first_two_joined = (words[0] + words[1]).lower()
                    author_last = author.split(',')[0].lower().replace('-', '').replace(' ', '')  # Use formatted author (Last, First)
                    if first_two_joined in author_last or author_last.startswith(first_two_joined):
                        # Skip first two words
                        potential_title = ' '.join(words[2:])
                # Clean spacing
                potential_title = re.sub(r'\s+', ' ', potential_title).strip()
                
                if 10 < len(potential_title) < 300:
                    title = potential_title
        
        # Alternative: Look for title pattern after author name
        if not title:
            # Try to find text that looks like a title (longer phrases with colons, etc.)
            lines = text.split('\n')
            title_candidates = []
            for i, line in enumerate(lines[:40]):
                line = line.strip()
                # Look for substantial lines that might be titles
                if 20 < len(line) < 200 and ':' in line:
                    title_candidates.append(line)
            
            if title_candidates:
                # Use the first candidate
                title = ' '.join(title_candidates[0].split())
    
    # Try to get title from PDF metadata if we don't have one yet
    if not title and pdf_metadata and '/Title' in pdf_metadata:
        metadata_title = str(pdf_metadata['/Title'])
        if metadata_title and metadata_title.lower() != 'untitled' and len(metadata_title) > 5:
            # Clean up metadata title (add spaces if needed)
            title = re.sub(r'([a-z])([A-Z])', r'\1 \2', metadata_title)
            title = re.sub(r',\s*', ': ', title, count=1)
    
    # If still no title, create one from author and year
    if not title:
        title = f"Student Scholarship by {author}"
    
    # Try to extract abstract or description from introduction
    abstract = ""
    if text:
        # Clean text for easier searching
        text_clean = ' '.join(text.split())
        
        # Look for abstract section with various patterns
        patterns = [
            (r'Abstract[:\s]+(.*?)(?:Genesis|Introduction|Keywords|Chapter)', 500),
            (r'(?:Intr oduction|Introduction)[:\s]+(.*?)(?:As I have|Recently|Further|Throughout|In this essay)', 500),
            (r'(?:Intr oduction|Introduction)[:\s]+(.{50,600})\.', 500),
        ]
        
        for pattern, max_len in patterns:
            match = re.search(pattern, text_clean, re.IGNORECASE)
            if match:
                abstract = match.group(1).strip()
                # Clean and take first sentences
                sentences = re.split(r'(?<=[.!?])\s+', abstract)
                if len(sentences) >= 3:
                    abstract = ' '.join(sentences[:4])
                    break
        
        if abstract:
            # Limit total length
            if len(abstract) > 500:
                abstract = abstract[:497]
                last_period = abstract.rfind('.')
                if last_period > 300:
                    abstract = abstract[:last_period+1]
                else:
                    abstract = abstract.rstrip() + "..."
    
    # If no abstract, create a basic description
    if not abstract or len(abstract) < 50:
        abstract = f"Student scholarship work by {author}, completed in {year} at Grinnell College."
    
    # Try to identify LCSH (Library of Congress Subject Headings) from title and content
    lcsh_subjects = []
    title_lower = title.lower()
    text_sample = (text[:2000].lower() if text else "")
    
    # Map keywords to proper LCSH subject headings
    lcsh_mappings = {
        'gender': ['Gender identity', 'Sex role'],
        'queer': ['Sexual minorities', 'Gender-nonconforming people'],
        'lgbtq': ['Sexual minorities', 'LGBTQ+ people'],
        'transgender': ['Transgender people'],
        'colonial': ['Colonialism', 'Postcolonialism'],
        'nigeria': ['Nigeria--History', 'Igbo (African people)'],
        'igbo': ['Igbo (African people)'],
        'african': ['Africa--Study and teaching'],
        'identity': ['Identity (Psychology)', 'Group identity'],
        'diaspora': ['Diaspora'],
        'race': ['Race relations', 'Racism'],
        'culture': ['Culture', 'Cross-cultural studies'],
        'history': ['History'],
        'sociology': ['Sociology'],
        'anthropology': ['Anthropology'],
        'ethnography': ['Ethnology'],
        'literature': ['Literature'],
        'politics': ['Political science'],
        'political': ['Political science'],
        'economics': ['Economics'],
        'environment': ['Environmental sciences'],
        'climate': ['Climatic changes'],
        'education': ['Education'],
        'student': ['Students', 'College students'],
        'scholarship': ['Scholarships'],
        'essay': ['Essays'],
        'research': ['Research']
    }
    
    # Collect matching LCSH terms
    for keyword, lcsh_terms in lcsh_mappings.items():
        if keyword in title_lower or keyword in text_sample:
            for term in lcsh_terms:
                if term not in lcsh_subjects:
                    lcsh_subjects.append(term)
                    if len(lcsh_subjects) >= 6:
                        break
        if len(lcsh_subjects) >= 6:
            break
    
    return {
        'filename': filename,
        'title': title,
        'author': author,
        'year': year,
        'abstract': abstract,
        'pages': page_count,
        'lcsh_subjects': lcsh_subjects
    }

def generate_metadata_csv(pdf_dir, output_csv, csv_headers):
    """Generate CSV with Dublin Core metadata for all PDFs"""
    
    # Get all PDF files (handle both underscore and space naming)
    all_files = os.listdir(pdf_dir)
    pdf_files = sorted([f for f in all_files if f.endswith('.pdf')])
    
    print(f"Found {len(pdf_files)} PDF files")
    
    # Prepare data rows
    rows = []
    
    for pdf_file in pdf_files:
        pdf_path = os.path.join(pdf_dir, pdf_file)
        print(f"Processing {pdf_file}...")
        
        # Extract text and analyze
        text = extract_text_from_pdf(pdf_path)
        metadata = analyze_pdf_content(pdf_path, text)
        
        # Create row with metadata mapped to CSV columns
        row = {}
        
        # Initialize all columns as empty
        for header in csv_headers:
            row[header] = ""
        
        # Map metadata to appropriate columns
        row['file_name_1'] = metadata['filename']
        row['dc:title'] = metadata['title']
        # Format creator as "Last, First (Class of YYYY)"
        row['dc:creator'] = f"{metadata['author']} (Class of {metadata['year']})"
        row['dc:date'] = metadata['year']
        row['dcterms:issued'] = metadata['year']
        row['dcterms:created'] = metadata['year']
        
        # Set type and format
        row['dc:type'] = "Text"
        row['dcterms:type.dcterms:DCMIType'] = "Text"
        row['dc:format'] = "application/pdf"
        row['dcterms:format.dcterms:IMT'] = "application/pdf"
        row['dc:language'] = "English"
        
        # Set extent and medium
        if metadata['pages'] > 0:
            row['dcterms:extent'] = f"{metadata['pages']} pages"
        row['dcterms:medium'] = "born digital"
        
        # Publisher
        row['dcterms:publisher'] = "Grinnell College"
        
        # Add description/abstract
        if metadata['abstract']:
            row['dc:description'] = metadata['abstract']
            row['dcterms:abstract'] = metadata['abstract']
        
        # Add LCSH subjects using pipe separator for multiple values
        if metadata.get('lcsh_subjects'):
            row['dcterms:subject.dcterms:LCSH'] = '|'.join(metadata['lcsh_subjects'])
            # Also add to general subject field
            row['dc:subject'] = '|'.join(metadata['lcsh_subjects'])
        
        # Add common "is part of" values (using pipe separator)
        row['dcterms:isPartOf'] = "Digital Grinnell|Scholarship at Grinnell|Student Scholarship"
        
        # Add rights statement
        row['dc:rights'] = "Copyright to this work is held by the author(s), in accordance with United States copyright law (USC 17). Readers of this work have certain rights as defined by the law, including but not limited to fair use (17 USC 107 et seq.)."
        
        # Add spatial coverage
        row['dcterms:spatial'] = "Grinnell, Iowa"
        
        # Add contributor (Grinnell College)
        row['dc:contributor'] = "Grinnell College"
        
        rows.append(row)
    
    # Write CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_headers)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nMetadata CSV generated: {output_csv}")
    print(f"Processed {len(rows)} PDF files")

def main():
    # Read CSV headers from the verified file
    headers_file = '/Users/mcfatem/GitHub/generate-metadata-using-Copilot/verified_CSV_headings_for_Alma-D.csv'
    with open(headers_file, 'r') as f:
        reader = csv.reader(f)
        csv_headers = next(reader)
    
    # Generate metadata CSV
    pdf_dir = '/Users/mcfatem/GitHub/generate-metadata-using-Copilot'
    output_csv = '/Users/mcfatem/GitHub/generate-metadata-using-Copilot/metadata_output.csv'
    
    generate_metadata_csv(pdf_dir, output_csv, csv_headers)

if __name__ == '__main__':
    main()
