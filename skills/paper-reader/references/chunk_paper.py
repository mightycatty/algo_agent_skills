#!/usr/bin/env python3
"""
Paper PDF Chunker

Extracts text from PDF and splits it into manageable chunks by sections.
Useful for processing large papers that exceed context window limits.

Usage:
    python chunk_paper.py <pdf_path> [output_dir] [--max-tokens N]

Examples:
    python chunk_paper.py paper.pdf
    python chunk_paper.py paper.pdf ./chunks/
    python chunk_paper.py paper.pdf ./chunks/ --max-tokens 3000

Requirements:
    pip install PyMuPDF  # or: pip install pymupdf
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

try:
    import fitz  # PyMuPDF
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False


# Common section headers in research papers
SECTION_PATTERNS = [
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Abstract|Introduction|Related\s+Work|Background)',
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Method(?:ology)?|Approach|(?:Proposed\s+)?(?:Method|Framework|Model))',
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Experiment(?:s|al)?(?:\s+(?:Setup|Results))?|Results|Evaluation)',
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Discussion|Analysis|Ablation(?:\s+Stud(?:y|ies))?)',
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Conclusion(?:s)?|Summary|Future\s+Work)',
    r'^(?:#{1,3}\s*)?(\d+\.?\s+)?(Appendix|Supplementary|References|Acknowledg(?:e)?ments?)',
]

# Priority mapping for sections
SECTION_PRIORITY = {
    'abstract': 0,
    'conclusion': 0,
    'introduction': 2,
    'method': 1,
    'methodology': 1,
    'approach': 1,
    'experiment': 1,
    'experiments': 1,
    'results': 1,
    'evaluation': 1,
    'related work': 2,
    'background': 2,
    'discussion': 2,
    'analysis': 2,
    'ablation': 2,
    'appendix': 3,
    'supplementary': 3,
    'references': 4,
    'acknowledgements': 4,
}


def estimate_tokens(text: str) -> int:
    """Rough token estimation (1 token ≈ 4 chars for English)."""
    return len(text) // 4


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    if not HAS_PYMUPDF:
        raise ImportError(
            "PyMuPDF is required for PDF processing.\n"
            "Install with: pip install PyMuPDF"
        )
    
    doc = fitz.open(pdf_path)
    text_parts = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text()
        text_parts.append(f"[PAGE {page_num + 1}]\n{text}")
    
    doc.close()
    return "\n\n".join(text_parts)


def identify_sections(text: str) -> List[Tuple[int, str, str]]:
    """
    Identify section boundaries in the text.
    
    Returns:
        List of (start_pos, section_name, normalized_name)
    """
    sections = []
    
    for line_start in range(len(text)):
        if line_start > 0 and text[line_start - 1] != '\n':
            continue
        
        # Find end of line
        line_end = text.find('\n', line_start)
        if line_end == -1:
            line_end = len(text)
        
        line = text[line_start:line_end].strip()
        
        # Skip empty or very long lines (not headers)
        if not line or len(line) > 100:
            continue
        
        # Check against section patterns
        for pattern in SECTION_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                # Extract section name
                section_name = line
                # Normalize for priority lookup
                normalized = re.sub(r'^\d+\.?\s*', '', line.lower())
                normalized = re.sub(r'[^\w\s]', '', normalized).strip()
                
                sections.append((line_start, section_name, normalized))
                break
    
    return sections


def split_into_chunks(
    text: str,
    sections: List[Tuple[int, str, str]],
    max_tokens: int = 3500
) -> List[Dict]:
    """
    Split text into chunks based on sections and token limits.
    
    Returns:
        List of chunk dictionaries with metadata
    """
    chunks = []
    
    if not sections:
        # No sections found, split by token count
        return split_by_tokens(text, max_tokens)
    
    # Add end position for each section
    section_ranges = []
    for i, (start, name, normalized) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else len(text)
        priority = SECTION_PRIORITY.get(normalized.split()[0] if normalized else '', 2)
        section_ranges.append({
            'start': start,
            'end': end,
            'name': name,
            'normalized': normalized,
            'priority': priority
        })
    
    # Group sections into chunks respecting token limits
    current_chunk = {
        'sections': [],
        'text': '',
        'priority': 999,
        'tokens': 0
    }
    
    for section in section_ranges:
        section_text = text[section['start']:section['end']]
        section_tokens = estimate_tokens(section_text)
        
        # If single section exceeds limit, split it
        if section_tokens > max_tokens:
            # Save current chunk if not empty
            if current_chunk['text']:
                chunks.append(current_chunk)
                current_chunk = {'sections': [], 'text': '', 'priority': 999, 'tokens': 0}
            
            # Split large section into sub-chunks
            sub_chunks = split_by_tokens(section_text, max_tokens, section['name'])
            for sc in sub_chunks:
                sc['priority'] = section['priority']
                sc['sections'] = [section['name']]
            chunks.extend(sub_chunks)
            continue
        
        # Check if adding this section exceeds limit
        if current_chunk['tokens'] + section_tokens > max_tokens and current_chunk['text']:
            chunks.append(current_chunk)
            current_chunk = {'sections': [], 'text': '', 'priority': 999, 'tokens': 0}
        
        # Add section to current chunk
        current_chunk['sections'].append(section['name'])
        current_chunk['text'] += section_text + '\n\n'
        current_chunk['priority'] = min(current_chunk['priority'], section['priority'])
        current_chunk['tokens'] += section_tokens
    
    # Don't forget the last chunk
    if current_chunk['text']:
        chunks.append(current_chunk)
    
    # Sort by priority
    chunks.sort(key=lambda x: x['priority'])
    
    # Add chunk indices
    for i, chunk in enumerate(chunks):
        chunk['index'] = i
        chunk['total'] = len(chunks)
    
    return chunks


def split_by_tokens(
    text: str,
    max_tokens: int,
    section_name: str = "content"
) -> List[Dict]:
    """Split text into chunks by token count, respecting paragraph boundaries."""
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_text = ''
    current_tokens = 0
    
    for para in paragraphs:
        para_tokens = estimate_tokens(para)
        
        if current_tokens + para_tokens > max_tokens and current_text:
            chunks.append({
                'sections': [section_name],
                'text': current_text.strip(),
                'tokens': current_tokens
            })
            current_text = ''
            current_tokens = 0
        
        current_text += para + '\n\n'
        current_tokens += para_tokens
    
    if current_text.strip():
        chunks.append({
            'sections': [section_name],
            'text': current_text.strip(),
            'tokens': current_tokens
        })
    
    return chunks


def save_chunks(
    chunks: List[Dict],
    output_dir: str,
    base_name: str
) -> List[str]:
    """Save chunks to individual files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    
    # Save manifest
    manifest = {
        'source': base_name,
        'total_chunks': len(chunks),
        'chunks': []
    }
    
    for chunk in chunks:
        # Create filename
        priority_label = ['P0', 'P1', 'P2', 'P3', 'P4'][min(chunk.get('priority', 2), 4)]
        chunk_name = f"{base_name}_chunk{chunk['index']:02d}_{priority_label}.txt"
        chunk_path = output_path / chunk_name
        
        # Write chunk content
        header = f"=== CHUNK {chunk['index'] + 1}/{chunk['total']} ===\n"
        header += f"Sections: {', '.join(chunk['sections'])}\n"
        header += f"Estimated tokens: {chunk['tokens']}\n"
        header += f"Priority: {priority_label}\n"
        header += "=" * 40 + "\n\n"
        
        with open(chunk_path, 'w', encoding='utf-8') as f:
            f.write(header + chunk['text'])
        
        saved_files.append(str(chunk_path))
        
        # Add to manifest
        manifest['chunks'].append({
            'file': chunk_name,
            'index': chunk['index'],
            'priority': priority_label,
            'sections': chunk['sections'],
            'tokens': chunk['tokens']
        })
    
    # Save manifest
    manifest_path = output_path / f"{base_name}_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    saved_files.append(str(manifest_path))
    
    return saved_files


def main():
    parser = argparse.ArgumentParser(
        description='Split PDF papers into manageable chunks for LLM processing'
    )
    parser.add_argument('pdf_path', help='Path to the PDF file')
    parser.add_argument('output_dir', nargs='?', default='./chunks',
                        help='Output directory for chunks (default: ./chunks)')
    parser.add_argument('--max-tokens', type=int, default=3500,
                        help='Maximum tokens per chunk (default: 3500)')
    
    args = parser.parse_args()
    
    if not HAS_PYMUPDF:
        print("Error: PyMuPDF is required. Install with: pip install PyMuPDF")
        sys.exit(1)
    
    if not os.path.exists(args.pdf_path):
        print(f"Error: PDF not found: {args.pdf_path}")
        sys.exit(1)
    
    print(f"Extracting text from: {args.pdf_path}")
    text = extract_text_from_pdf(args.pdf_path)
    print(f"Extracted {len(text)} characters (~{estimate_tokens(text)} tokens)")
    
    print("Identifying sections...")
    sections = identify_sections(text)
    print(f"Found {len(sections)} sections")
    
    print(f"Splitting into chunks (max {args.max_tokens} tokens)...")
    chunks = split_into_chunks(text, sections, args.max_tokens)
    print(f"Created {len(chunks)} chunks")
    
    base_name = Path(args.pdf_path).stem
    saved_files = save_chunks(chunks, args.output_dir, base_name)
    
    print(f"\nSaved {len(saved_files)} files to: {args.output_dir}")
    print("\nChunk summary:")
    for chunk in chunks:
        priority = ['P0-Must', 'P1-High', 'P2-Medium', 'P3-Low', 'P4-Skip'][min(chunk.get('priority', 2), 4)]
        sections_str = ', '.join(chunk['sections'][:2])
        if len(chunk['sections']) > 2:
            sections_str += f" (+{len(chunk['sections'])-2} more)"
        print(f"  Chunk {chunk['index']+1}: {priority:10} | {chunk['tokens']:5} tokens | {sections_str}")


if __name__ == "__main__":
    main()
