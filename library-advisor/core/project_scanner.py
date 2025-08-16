import os
import json
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import git

@dataclass
class ProjectFile:
    """Represents a file in the project"""
    path: str
    content: str
    file_type: str
    size: int
    chunks: List[str] = None

@dataclass
class ProjectProfile:
    """Represents the analyzed project profile"""
    project_id: str
    name: str
    framework: str
    dependencies: Dict[str, str]
    files: List[ProjectFile]
    total_files: int
    total_size: int
    languages: List[str]

class ProjectScanner:
    """Scans and analyzes project directories"""
    
    def __init__(self, supported_extensions: List[str]):
        self.supported_extensions = [ext.lower() for ext in supported_extensions]
        self.chunk_size = 1000  # characters per chunk
        self.overlap = 200  # overlap between chunks
        
    def scan_project_directory(self, project_path: str) -> ProjectProfile:
        """
        Scan and analyze a project directory
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProjectProfile: Analyzed project profile
        """
        project_path = Path(project_path)
        project_id = self._generate_project_id(str(project_path))
        
        # Scan files
        files = self._scan_files(project_path)
        
        # Extract dependencies
        dependencies = self._extract_dependencies(files)
        
        # Detect framework
        framework = self._detect_framework(files, dependencies)
        
        # Detect languages
        languages = self._detect_languages(files)
        
        # Calculate totals
        total_size = sum(f.size for f in files)
        
        return ProjectProfile(
            project_id=project_id,
            name=project_path.name,
            framework=framework,
            dependencies=dependencies,
            files=files,
            total_files=len(files),
            total_size=total_size,
            languages=languages
        )
    
    def _scan_files(self, project_path: Path) -> List[ProjectFile]:
        """Scan files in the project directory"""
        files = []
        
        # Skip common ignore patterns
        ignore_patterns = {
            'node_modules', 'bin', 'obj', '.git', '.vs', '.vscode',
            'dist', 'build', '__pycache__', '.pytest_cache',
            'coverage', '.nyc_output'
        }
        
        for root, dirs, filenames in os.walk(project_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_patterns]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Check if file extension is supported
                if file_path.suffix.lower() in self.supported_extensions:
                    try:
                        content = self._read_file_safely(file_path)
                        if content:
                            file_obj = ProjectFile(
                                path=str(file_path.relative_to(project_path)),
                                content=content,
                                file_type=self._get_file_type(file_path),
                                size=len(content)
                            )
                            
                            # Chunk the content
                            file_obj.chunks = self._chunk_content(content)
                            files.append(file_obj)
                            
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
                        continue
        
        return files
    
    def _read_file_safely(self, file_path: Path) -> Optional[str]:
        """Safely read file content with encoding detection"""
        encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception:
                break
        
        return None
    
    def _chunk_content(self, content: str) -> List[str]:
        """Split content into chunks with overlap"""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            
            # Try to break at a natural boundary (newline, sentence, etc.)
            if end < len(content):
                # Look for natural break points
                for break_char in ['\n\n', '\n', '.', ';', '}', '{']:
                    break_pos = content.rfind(break_char, start, end)
                    if break_pos > start + self.chunk_size // 2:
                        end = break_pos + len(break_char)
                        break
            
            chunks.append(content[start:end].strip())
            start = max(start + 1, end - self.overlap)
        
        return [chunk for chunk in chunks if chunk]
    
    def _extract_dependencies(self, files: List[ProjectFile]) -> Dict[str, str]:
        """Extract dependencies from project files"""
        dependencies = {}
        
        for file in files:
            if file.path.endswith('package.json'):
                deps = self._extract_npm_dependencies(file.content)
                dependencies.update(deps)
            elif file.path.endswith('.csproj'):
                deps = self._extract_csproj_dependencies(file.content)
                dependencies.update(deps)
            elif file.path.endswith('requirements.txt'):
                deps = self._extract_pip_dependencies(file.content)
                dependencies.update(deps)
        
        return dependencies
    
    def _extract_npm_dependencies(self, content: str) -> Dict[str, str]:
        """Extract dependencies from package.json"""
        try:
            data = json.loads(content)
            dependencies = {}
            
            for dep_type in ['dependencies', 'devDependencies', 'peerDependencies']:
                if dep_type in data:
                    dependencies.update(data[dep_type])
            
            return dependencies
        except json.JSONDecodeError as e:
            print(f"JSON decode error in package.json: {e}")
            return {}
    
    def _extract_csproj_dependencies(self, content: str) -> Dict[str, str]:
        """Extract dependencies from .csproj files"""
        try:
            root = ET.fromstring(content)
            dependencies = {}
            
            # Find PackageReference elements
            for package_ref in root.findall('.//PackageReference'):
                name = package_ref.get('Include')
                version = package_ref.get('Version', 'latest')
                if name:
                    dependencies[name] = version
            
            return dependencies
        except ET.ParseError:
            return {}
    
    def _extract_pip_dependencies(self, content: str) -> Dict[str, str]:
        """Extract dependencies from requirements.txt"""
        dependencies = {}
        
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Parse package==version format
                if '==' in line:
                    name, version = line.split('==', 1)
                    dependencies[name.strip()] = version.strip()
                else:
                    dependencies[line] = 'latest'
        
        return dependencies
    
    def _detect_framework(self, files: List[ProjectFile], dependencies: Dict[str, str]) -> str:
        """Detect the primary framework used in the project"""
        framework_indicators = {
            'React': ['react', 'react-dom', '@types/react'],
            'Vue.js': ['vue', '@vue/cli', 'vue-router', 'vuex'],
            '.NET': ['Microsoft.AspNetCore', 'Microsoft.EntityFrameworkCore', 'System.'],
            'Angular': ['@angular/core', '@angular/cli'],
            'Next.js': ['next', 'react'],
            'Express.js': ['express'],
            'FastAPI': ['fastapi'],
            'Django': ['django'],
            'Flask': ['flask']
        }
        
        # Check dependencies first
        for framework, indicators in framework_indicators.items():
            if any(dep in dependencies for dep in indicators):
                return framework
        
        # Check file extensions and content
        file_extensions = [f.file_type for f in files]
        
        if any(ext in file_extensions for ext in ['tsx', 'jsx']):
            return 'React'
        elif any(ext in file_extensions for ext in ['vue']):
            return 'Vue.js'
        elif any(ext in file_extensions for ext in ['cs', 'csproj']):
            return '.NET'
        elif any(ext in file_extensions for ext in ['py']):
            return 'Python'
        elif any(ext in file_extensions for ext in ['js', 'ts']):
            return 'JavaScript/TypeScript'
        
        return 'Unknown'
    
    def _detect_languages(self, files: List[ProjectFile]) -> List[str]:
        """Detect programming languages used in the project"""
        language_map = {
            'js': 'JavaScript',
            'ts': 'TypeScript',
            'jsx': 'JavaScript (React)',
            'tsx': 'TypeScript (React)',
            'vue': 'Vue.js',
            'cs': 'C#',
            'py': 'Python',
            'html': 'HTML',
            'css': 'CSS',
            'scss': 'SCSS',
            'json': 'JSON',
            'xml': 'XML',
            'md': 'Markdown'
        }
        
        languages = set()
        for file in files:
            if file.file_type in language_map:
                languages.add(language_map[file.file_type])
        
        return list(languages)
    
    def _get_file_type(self, file_path: Path) -> str:
        """Get file type from extension"""
        return file_path.suffix.lstrip('.').lower()
    
    def _generate_project_id(self, project_path: str) -> str:
        """Generate unique project ID"""
        return hashlib.md5(project_path.encode()).hexdigest()[:8]
