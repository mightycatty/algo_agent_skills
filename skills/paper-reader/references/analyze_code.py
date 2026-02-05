#!/usr/bin/env python3
"""
Source Code Analyzer for Paper Reader Skill

Analyzes source code repositories to extract model architecture information
in a context-window friendly format.

Features:
- Skeleton scan: Extract file tree + class/function signatures
- Priority-based extraction: Focus on core model files first
- Chunked output: Split large codebases into manageable pieces

Usage:
    python analyze_code.py <source_dir> [output_dir] [--mode skeleton|full|targeted]
    
Examples:
    # Skeleton scan (default) - get structure overview
    python analyze_code.py ./bert_code ./output
    
    # Full extraction with priority chunks
    python analyze_code.py ./bert_code ./output --mode full
    
    # Targeted extraction for specific classes
    python analyze_code.py ./bert_code ./output --mode targeted --targets "BertAttention,BertModel"
"""

import os
import re
import ast
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict


# =============================================================================
# Configuration
# =============================================================================

# File priority patterns (P0 = highest priority)
FILE_PRIORITY = {
    0: [r'modeling_.*\.py$', r'model\.py$', r'models\.py$'],
    1: [r'config.*\.py$', r'attention.*\.py$', r'transformer.*\.py$'],
    2: [r'layers?\.py$', r'modules?\.py$', r'embeddings?\.py$'],
    3: [r'train.*\.py$', r'.*_utils\.py$', r'utils\.py$'],
}

# Files/directories to skip
SKIP_PATTERNS = [
    r'__pycache__',
    r'\.git',
    r'\.pyc$',
    r'test_.*\.py$',
    r'.*_test\.py$',
    r'setup\.py$',
    r'__init__\.py$',  # Usually just imports
]

# Target token limits per chunk
DEFAULT_MAX_TOKENS = 4000
TOKENS_PER_CHAR = 0.25  # Rough estimate


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ClassInfo:
    name: str
    bases: List[str]
    methods: List[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    
@dataclass
class FunctionInfo:
    name: str
    args: str
    returns: Optional[str]
    docstring: Optional[str]
    line_start: int
    line_end: int
    decorators: List[str]

@dataclass
class FileInfo:
    path: str
    priority: int
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    imports: List[str]
    total_lines: int


# =============================================================================
# AST Parser
# =============================================================================

class CodeAnalyzer:
    """Analyzes Python source files using AST."""
    
    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.files: List[FileInfo] = []
        
    def should_skip(self, path: str) -> bool:
        """Check if file/directory should be skipped."""
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, path):
                return True
        return False
    
    def get_priority(self, filename: str) -> int:
        """Determine file priority (lower = more important)."""
        for priority, patterns in FILE_PRIORITY.items():
            for pattern in patterns:
                if re.search(pattern, filename):
                    return priority
        return 99  # Default: lowest priority
    
    def parse_file(self, filepath: Path) -> Optional[FileInfo]:
        """Parse a single Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                source = f.read()
            
            tree = ast.parse(source)
            lines = source.split('\n')
            
            classes = []
            functions = []
            imports = []
            
            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    names = ', '.join(alias.name for alias in node.names[:5])
                    if len(node.names) > 5:
                        names += ', ...'
                    imports.append(f"from {module} import {names}")
            
            # Top-level classes and functions only
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(self._parse_class(node))
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    functions.append(self._parse_function(node))
            
            rel_path = str(filepath.relative_to(self.source_dir))
            priority = self.get_priority(filepath.name)
            
            return FileInfo(
                path=rel_path,
                priority=priority,
                classes=classes,
                functions=functions,
                imports=imports[:10],  # Limit imports
                total_lines=len(lines)
            )
            
        except SyntaxError as e:
            print(f"  [WARN] Syntax error in {filepath}: {e}")
            return None
        except Exception as e:
            print(f"  [WARN] Error parsing {filepath}: {e}")
            return None
    
    def _parse_class(self, node: ast.ClassDef) -> ClassInfo:
        """Extract class information."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{self._get_attr_name(base)}")
        
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Include method signature
                args = self._format_args(item.args)
                methods.append(f"{item.name}({args})")
        
        docstring = ast.get_docstring(node)
        if docstring and len(docstring) > 200:
            docstring = docstring[:200] + "..."
        
        return ClassInfo(
            name=node.name,
            bases=bases,
            methods=methods,
            docstring=docstring,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno
        )
    
    def _parse_function(self, node) -> FunctionInfo:
        """Extract function information."""
        args = self._format_args(node.args)
        
        returns = None
        if node.returns:
            returns = self._get_annotation(node.returns)
        
        decorators = []
        for dec in node.decorator_list:
            if isinstance(dec, ast.Name):
                decorators.append(f"@{dec.id}")
            elif isinstance(dec, ast.Attribute):
                decorators.append(f"@{self._get_attr_name(dec)}")
        
        docstring = ast.get_docstring(node)
        if docstring and len(docstring) > 150:
            docstring = docstring[:150] + "..."
        
        return FunctionInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=docstring,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            decorators=decorators
        )
    
    def _format_args(self, args: ast.arguments) -> str:
        """Format function arguments."""
        parts = []
        
        # Regular args
        for arg in args.args[:6]:  # Limit to first 6 args
            if arg.annotation:
                parts.append(f"{arg.arg}: {self._get_annotation(arg.annotation)}")
            else:
                parts.append(arg.arg)
        
        if len(args.args) > 6:
            parts.append("...")
        
        # *args and **kwargs
        if args.vararg:
            parts.append(f"*{args.vararg.arg}")
        if args.kwarg:
            parts.append(f"**{args.kwarg.arg}")
        
        return ", ".join(parts)
    
    def _get_annotation(self, node) -> str:
        """Get type annotation as string."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.Subscript):
            return f"{self._get_annotation(node.value)}[...]"
        elif isinstance(node, ast.Attribute):
            return self._get_attr_name(node)
        return "Any"
    
    def _get_attr_name(self, node: ast.Attribute) -> str:
        """Get full attribute name (e.g., nn.Module)."""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return ".".join(reversed(parts))
    
    def scan_directory(self) -> List[FileInfo]:
        """Scan all Python files in directory."""
        print(f"Scanning: {self.source_dir}")
        
        for root, dirs, files in os.walk(self.source_dir):
            # Filter directories
            dirs[:] = [d for d in dirs if not self.should_skip(d)]
            
            for filename in files:
                if not filename.endswith('.py'):
                    continue
                    
                filepath = Path(root) / filename
                rel_path = str(filepath.relative_to(self.source_dir))
                
                if self.should_skip(rel_path):
                    continue
                
                file_info = self.parse_file(filepath)
                if file_info:
                    self.files.append(file_info)
                    print(f"  [P{file_info.priority}] {rel_path} ({len(file_info.classes)} classes, {len(file_info.functions)} functions)")
        
        # Sort by priority
        self.files.sort(key=lambda x: (x.priority, x.path))
        return self.files


# =============================================================================
# Output Generators
# =============================================================================

class OutputGenerator:
    """Generates various output formats."""
    
    def __init__(self, files: List[FileInfo], output_dir: str, max_tokens: int = DEFAULT_MAX_TOKENS):
        self.files = files
        self.output_dir = Path(output_dir)
        self.max_tokens = max_tokens
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text."""
        return int(len(text) * TOKENS_PER_CHAR)
    
    def generate_skeleton(self) -> str:
        """Generate skeleton view (structure only, no implementations)."""
        lines = []
        lines.append("# Code Structure Skeleton\n")
        lines.append("## File Tree\n```")
        
        # File tree
        for f in self.files:
            priority_marker = f"[P{f.priority}]" if f.priority < 99 else ""
            lines.append(f"{priority_marker} {f.path} ({f.total_lines} lines)")
        lines.append("```\n")
        
        # Class/function signatures by priority
        lines.append("## Signatures by Priority\n")
        
        current_priority = -1
        for f in self.files:
            if f.priority != current_priority:
                current_priority = f.priority
                lines.append(f"\n### Priority {current_priority}\n")
            
            if f.classes or f.functions:
                lines.append(f"\n#### `{f.path}`\n```python")
                
                for cls in f.classes:
                    bases = f"({', '.join(cls.bases)})" if cls.bases else ""
                    lines.append(f"class {cls.name}{bases}:")
                    for method in cls.methods[:10]:  # Limit methods shown
                        lines.append(f"    def {method}: ...")
                    if len(cls.methods) > 10:
                        lines.append(f"    # ... {len(cls.methods) - 10} more methods")
                    lines.append("")
                
                for func in f.functions:
                    decs = "\n".join(func.decorators)
                    if decs:
                        lines.append(decs)
                    ret = f" -> {func.returns}" if func.returns else ""
                    lines.append(f"def {func.name}({func.args}){ret}: ...")
                
                lines.append("```")
        
        skeleton = "\n".join(lines)
        
        # Save skeleton
        skeleton_path = self.output_dir / "skeleton.md"
        with open(skeleton_path, 'w', encoding='utf-8') as f:
            f.write(skeleton)
        
        print(f"\nSkeleton saved: {skeleton_path} (~{self.estimate_tokens(skeleton)} tokens)")
        return skeleton
    
    def generate_chunks(self, source_dir: Path) -> List[Dict]:
        """Generate prioritized chunks with full source code."""
        chunks = []
        current_chunk = []
        current_tokens = 0
        current_priority = 0
        chunk_index = 0
        
        for file_info in self.files:
            # Read full source
            filepath = source_dir / file_info.path
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    source = f.read()
            except:
                continue
            
            file_content = f"# File: {file_info.path}\n# Priority: P{file_info.priority}\n# Lines: {file_info.total_lines}\n\n{source}"
            file_tokens = self.estimate_tokens(file_content)
            
            # Check if we need a new chunk
            if current_tokens + file_tokens > self.max_tokens and current_chunk:
                # Save current chunk
                chunk_text = "\n\n" + "="*60 + "\n\n".join(current_chunk)
                chunk_name = f"chunk_{chunk_index:02d}_P{current_priority}.md"
                chunk_path = self.output_dir / chunk_name
                
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk_text)
                
                chunks.append({
                    "index": chunk_index,
                    "priority": current_priority,
                    "filename": chunk_name,
                    "files": [c.split('\n')[0].replace('# File: ', '') for c in current_chunk],
                    "tokens": current_tokens
                })
                
                print(f"  Chunk {chunk_index}: P{current_priority}, {len(current_chunk)} files, ~{current_tokens} tokens")
                
                current_chunk = []
                current_tokens = 0
                chunk_index += 1
            
            current_chunk.append(file_content)
            current_tokens += file_tokens
            current_priority = file_info.priority
        
        # Save last chunk
        if current_chunk:
            chunk_text = "\n\n" + "="*60 + "\n\n".join(current_chunk)
            chunk_name = f"chunk_{chunk_index:02d}_P{current_priority}.md"
            chunk_path = self.output_dir / chunk_name
            
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk_text)
            
            chunks.append({
                "index": chunk_index,
                "priority": current_priority,
                "filename": chunk_name,
                "files": [c.split('\n')[0].replace('# File: ', '') for c in current_chunk],
                "tokens": current_tokens
            })
            
            print(f"  Chunk {chunk_index}: P{current_priority}, {len(current_chunk)} files, ~{current_tokens} tokens")
        
        return chunks
    
    def generate_manifest(self, chunks: List[Dict]) -> None:
        """Generate manifest file with chunk index."""
        manifest = {
            "total_files": len(self.files),
            "total_chunks": len(chunks),
            "priority_distribution": {},
            "chunks": chunks
        }
        
        # Count files by priority
        for f in self.files:
            p = f"P{f.priority}"
            manifest["priority_distribution"][p] = manifest["priority_distribution"].get(p, 0) + 1
        
        manifest_path = self.output_dir / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"\nManifest saved: {manifest_path}")


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Analyze source code for paper-reader skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("source_dir", help="Source code directory to analyze")
    parser.add_argument("output_dir", nargs="?", default="./code_analysis", 
                        help="Output directory (default: ./code_analysis)")
    parser.add_argument("--mode", choices=["skeleton", "full", "targeted"], 
                        default="skeleton",
                        help="Analysis mode: skeleton (signatures only), full (with source), targeted (specific classes)")
    parser.add_argument("--targets", type=str, default="",
                        help="Comma-separated class/function names for targeted mode")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"Max tokens per chunk (default: {DEFAULT_MAX_TOKENS})")
    
    args = parser.parse_args()
    
    source_dir = Path(args.source_dir)
    if not source_dir.exists():
        print(f"Error: Source directory not found: {source_dir}")
        return 1
    
    print("="*60)
    print("Source Code Analyzer for Paper Reader")
    print("="*60)
    
    # Analyze
    analyzer = CodeAnalyzer(str(source_dir))
    files = analyzer.scan_directory()
    
    if not files:
        print("No Python files found!")
        return 1
    
    print(f"\nFound {len(files)} Python files")
    
    # Generate output
    generator = OutputGenerator(files, args.output_dir, args.max_tokens)
    
    print("\n" + "-"*40)
    print("Generating skeleton...")
    generator.generate_skeleton()
    
    if args.mode == "full":
        print("\n" + "-"*40)
        print("Generating full source chunks...")
        chunks = generator.generate_chunks(source_dir)
        generator.generate_manifest(chunks)
    
    print("\n" + "="*60)
    print("Analysis complete!")
    print(f"Output directory: {args.output_dir}")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    exit(main())
