import os
import re
from typing import List, Dict, Optional
from pathlib import Path

def validate_file_path(file_path: str) -> bool:
    """Validate that a file path is safe and exists"""
    try:
        path = Path(file_path)
        
        # Check if path exists
        if not path.exists():
            return False
        
        # Check for path traversal attacks
        resolved_path = path.resolve()
        if '..' in str(resolved_path):
            return False
            
        return True
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def validate_project_structure(project_path: str) -> Dict[str, any]:
    """Validate project structure and detect potential issues"""
    project_path = Path(project_path)
    issues = []
    warnings = []
    
    # Check if path exists
    if not project_path.exists():
        issues.append(f"Project path does not exist: {project_path}")
        return {'valid': False, 'issues': issues, 'warnings': warnings}
    
    # Check if it's a directory
    if not project_path.is_dir():
        issues.append(f"Project path is not a directory: {project_path}")
        return {'valid': False, 'issues': issues, 'warnings': warnings}
    
    # Check for common project files
    common_files = ['package.json', '*.csproj', '*.sln', 'requirements.txt', 'Dockerfile']
    found_project_files = []
    
    for pattern in common_files:
        if '*' in pattern:
            matches = list(project_path.glob(pattern))
            found_project_files.extend([f.name for f in matches])
        else:
            if (project_path / pattern).exists():
                found_project_files.append(pattern)
    
    if not found_project_files:
        warnings.append("No common project files found (package.json, *.csproj, etc.)")
    
    # Check project size (warn if too large)
    total_size = sum(f.stat().st_size for f in project_path.rglob('*') if f.is_file())
    if total_size > 500 * 1024 * 1024:  # 500MB
        warnings.append(f"Project is very large ({total_size / (1024*1024):.1f}MB). Processing may be slow.")
    
    # Check for too many files
    file_count = len(list(project_path.rglob('*')))
    if file_count > 10000:
        warnings.append(f"Project contains many files ({file_count}). Consider using .gitignore patterns.")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues,
        'warnings': warnings,
        'project_files': found_project_files,
        'total_size': total_size,
        'file_count': file_count
    }

def extract_code_context(content: str, target_line: int, context_lines: int = 3) -> str:
    """Extract code context around a target line"""
    lines = content.split('\n')
    start_line = max(0, target_line - context_lines - 1)
    end_line = min(len(lines), target_line + context_lines)
    
    context = []
    for i in range(start_line, end_line):
        prefix = ">>> " if i == target_line - 1 else "    "
        context.append(f"{prefix}{i+1:4d}: {lines[i]}")
    
    return '\n'.join(context)

def parse_version_string(version: str) -> Optional[Dict[str, int]]:
    """Parse version string into components"""
    # Handle common version formats: 1.2.3, ^1.2.3, ~1.2.3, >=1.2.3
    version_clean = re.sub(r'^[\^~>=<]+', '', version)
    
    # Extract major.minor.patch
    match = re.match(r'^(\d+)(?:\.(\d+))?(?:\.(\d+))?', version_clean)
    
    if match:
        major = int(match.group(1))
        minor = int(match.group(2)) if match.group(2) else 0
        patch = int(match.group(3)) if match.group(3) else 0
        
        return {'major': major, 'minor': minor, 'patch': patch}
    
    return None

def compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings. Returns -1, 0, or 1"""
    v1 = parse_version_string(version1)
    v2 = parse_version_string(version2)
    
    if not v1 or not v2:
        return 0  # Can't compare
    
    for component in ['major', 'minor', 'patch']:
        if v1[component] < v2[component]:
            return -1
        elif v1[component] > v2[component]:
            return 1
    
    return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

def is_text_file(file_path: str) -> bool:
    """Check if file is likely a text file"""
    text_extensions = {
        '.txt', '.md', '.py', '.js', '.ts', '.jsx', '.tsx',
        '.css', '.scss', '.html', '.xml', '.json', '.yaml', '.yml',
        '.cs', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go',
        '.sql', '.sh', '.bash', '.ps1', '.bat', '.dockerfile',
        '.gitignore', '.env', '.config'
    }
    
    file_path = Path(file_path)
    
    # Check extension
    if file_path.suffix.lower() in text_extensions:
        return True
    
    # Check if filename suggests text file
    text_filenames = {'readme', 'license', 'changelog', 'dockerfile', 'makefile'}
    if file_path.name.lower() in text_filenames:
        return True
    
    try:
        # Try to read first few bytes to detect binary
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            
        # If we find null bytes, it's likely binary
        if b'\x00' in chunk:
            return False
        
        # Try to decode as text
        chunk.decode('utf-8')
        return True
        
    except (UnicodeDecodeError, FileNotFoundError, PermissionError):
        return False

def clean_code_content(content: str) -> str:
    """Clean code content for better processing"""
    # Remove excessive whitespace
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
    
    # Remove very long lines (likely minified code)
    lines = content.split('\n')
    cleaned_lines = []
    
    for line in lines:
        if len(line) > 500:
            # Truncate very long lines
            cleaned_lines.append(line[:500] + '...')
        else:
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)

def extract_imports_from_content(content: str, language: str) -> List[str]:
    """Extract import statements from code content"""
    imports = []
    
    patterns = {
        'javascript': [
            r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
            r'require\([\'"]([^\'"]+)[\'"]\)',
        ],
        'python': [
            r'from\s+([^\s]+)\s+import',
            r'import\s+([^\s,]+)',
        ],
        'csharp': [
            r'using\s+([^;]+);',
        ]
    }
    
    if language in patterns:
        for pattern in patterns[language]:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
    
    return imports
