# Project Prompt: Generate Dublin Core Metadata for PDFs

## Objective

Generate Dublin Core (dc:) and Extended Dublin Core (dcterms:) descriptive metadata for 7 PDF documents and output to a CSV file for Alma-D import.

## Requirements

### Input
- 7 PDF files in the repository
- Reference structure: https://grinnell.primo.exlibrisgroup.com/permalink/01GCL_INST/1prvshj/alma991011593352104641

### Output CSV Structure
- Use column headings from `verified_CSV_headings_for_Alma-D.csv` (53 columns)
- Separate multiple values within fields using `|` character (not semicolons)
- Place PDF filename in `file_name_1` column

### Metadata Fields to Populate

**Required Fields:**
- `file_name_1`: PDF filename
- `dc:title`: Document title (extract from PDF or generate from author/year)
- `dc:creator`: Format as "Last, First (Class of YYYY)" where YYYY is the year from filename
- `dc:date`, `dcterms:issued`, `dcterms:created`: Year from filename
- `dc:type`, `dcterms:type.dcterms:DCMIType`: "Text"
- `dc:format`, `dcterms:format.dcterms:IMT`: "application/pdf"
- `dc:language`: "English"
- `dcterms:extent`: Page count
- `dcterms:medium`: "born digital"
- `dcterms:publisher`: "Grinnell College"
- `dc:contributor`: "Grinnell College"

**Descriptive Fields:**
- `dc:description`, `dcterms:abstract`: Extract from PDF introduction when available
- `dc:subject`, `dcterms:subject.dcterms:LCSH`: Library of Congress Subject Headings based on content analysis
- `dcterms:isPartOf`: "Digital Grinnell|Scholarship at Grinnell|Student Scholarship"
- `dcterms:spatial`: "Grinnell, Iowa"
- `dc:rights`: Standard copyright statement for student work

### Special Instructions

1. **Creator Format**: Parse names from filenames and format as "Last, First (Class of YYYY)"
   - Handle hyphenated surnames (e.g., "Willig-Onwuachi")
   - Preserve middle names/initials (e.g., "Allan, Elizabeth A.")

2. **Title Extraction**: Attempt to extract actual titles from PDFs
   - Check for pipe-delimited format: `| Title |`
   - Check for quoted titles: `"Title"`
   - Handle multi-line titles
   - Remove author name fragments
   - Fall back to "Student Scholarship by [Name]" if extraction fails

3. **LCSH Subject Headings**: Assign proper Library of Congress Subject Headings
   - Analyze content and title for keywords
   - Map to appropriate LCSH terms (e.g., "Gender identity", "Sexual minorities", "Colonialism")
   - Default to "Students|College students|Scholarships" for general student work

4. **Abstract Extraction**: Extract from introduction or abstract section when text is available
   - Look for "Abstract:" or "Introduction" sections
   - Take first 3-4 sentences, limit to ~500 characters
   - Use generic description for scanned documents

5. **File Handling**: Support both filename formats
   - Underscore format: `YYYY_First_Last.pdf`
   - Space format: `YYYY First Last.pdf`

## Implementation Notes

- Use PyPDF2 for PDF text extraction
- Handle scanned PDFs (no extractable text) gracefully
- Generate output file: `metadata_output.csv`
- Ensure all 53 columns are present in output
