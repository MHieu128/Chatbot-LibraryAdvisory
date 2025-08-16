import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

class FileParser:
    """Utility class for parsing different file types"""
    
    @staticmethod
    def parse_package_json(content: str) -> Dict[str, Any]:
        """Parse package.json file"""
        try:
            data = json.loads(content)
            return {
                'name': data.get('name', ''),
                'version': data.get('version', ''),
                'description': data.get('description', ''),
                'dependencies': data.get('dependencies', {}),
                'dev_dependencies': data.get('devDependencies', {}),
                'peer_dependencies': data.get('peerDependencies', {}),
                'scripts': data.get('scripts', {}),
                'keywords': data.get('keywords', []),
                'author': data.get('author', ''),
                'license': data.get('license', '')
            }
        except json.JSONDecodeError:
            return {}
    
    @staticmethod
    def parse_csproj(content: str) -> Dict[str, Any]:
        """Parse .csproj file"""
        try:
            root = ET.fromstring(content)
            
            # Extract basic properties
            project_info = {}
            
            # Get target framework
            target_framework = root.find('.//TargetFramework')
            if target_framework is not None:
                project_info['target_framework'] = target_framework.text
            
            # Get package references
            package_refs = {}
            for package_ref in root.findall('.//PackageReference'):
                name = package_ref.get('Include')
                version = package_ref.get('Version', 'latest')
                if name:
                    package_refs[name] = version
            
            project_info['package_references'] = package_refs
            
            # Get project references
            project_refs = []
            for project_ref in root.findall('.//ProjectReference'):
                include = project_ref.get('Include')
                if include:
                    project_refs.append(include)
            
            project_info['project_references'] = project_refs
            
            return project_info
            
        except ET.ParseError:
            return {}
    
    @staticmethod
    def parse_requirements_txt(content: str) -> Dict[str, str]:
        """Parse requirements.txt file"""
        requirements = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse different requirement formats
            if '==' in line:
                name, version = line.split('==', 1)
                requirements[name.strip()] = version.strip()
            elif '>=' in line:
                name, version = line.split('>=', 1)
                requirements[name.strip()] = f">={version.strip()}"
            elif '<=' in line:
                name, version = line.split('<=', 1)
                requirements[name.strip()] = f"<={version.strip()}"
            else:
                # No version specified
                requirements[line] = 'latest'
        
        return requirements
    
    @staticmethod
    def parse_dockerfile(content: str) -> Dict[str, Any]:
        """Parse Dockerfile"""
        info = {
            'base_image': '',
            'exposed_ports': [],
            'environment_vars': {},
            'installed_packages': []
        }
        
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('FROM '):
                info['base_image'] = line[5:].strip()
            
            elif line.startswith('EXPOSE '):
                ports = line[7:].strip().split()
                info['exposed_ports'].extend(ports)
            
            elif line.startswith('ENV '):
                env_part = line[4:].strip()
                if '=' in env_part:
                    key, value = env_part.split('=', 1)
                    info['environment_vars'][key.strip()] = value.strip()
            
            elif line.startswith('RUN ') and ('apt-get install' in line or 'yum install' in line or 'pip install' in line):
                # Extract package installation commands
                info['installed_packages'].append(line[4:].strip())
        
        return info
    
    @staticmethod
    def parse_yaml_config(content: str) -> Dict[str, Any]:
        """Parse YAML configuration files"""
        try:
            import yaml
            return yaml.safe_load(content) or {}
        except ImportError:
            # Fallback to simple parsing if PyYAML is not available
            return FileParser._simple_yaml_parse(content)
        except yaml.YAMLError:
            return {}
    
    @staticmethod
    def _simple_yaml_parse(content: str) -> Dict[str, Any]:
        """Simple YAML parsing fallback"""
        result = {}
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                if value.isdigit():
                    value = int(value)
                elif value.lower() in ('true', 'false'):
                    value = value.lower() == 'true'
                
                result[key] = value
        
        return result
    
    @staticmethod
    def extract_dependencies_from_code(content: str, file_type: str) -> List[str]:
        """Extract dependencies from code files"""
        dependencies = []
        
        if file_type in ['js', 'jsx', 'ts', 'tsx']:
            # JavaScript/TypeScript imports
            import_patterns = [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'import\([\'"]([^\'"]+)[\'"]\)',
                r'require\([\'"]([^\'"]+)[\'"]\)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)
        
        elif file_type == 'py':
            # Python imports
            import_patterns = [
                r'from\s+([^\s]+)\s+import',
                r'import\s+([^\s,]+)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content, re.MULTILINE)
                dependencies.extend(matches)
        
        elif file_type == 'cs':
            # C# using statements
            using_pattern = r'using\s+([^;]+);'
            matches = re.findall(using_pattern, content, re.MULTILINE)
            dependencies.extend(matches)
        
        # Filter out relative imports and standard library modules
        filtered_deps = []
        for dep in dependencies:
            dep = dep.strip()
            
            # Skip relative imports
            if dep.startswith('.') or dep.startswith('/'):
                continue
            
            # Skip standard library modules (basic check)
            if file_type == 'py' and dep in ['os', 'sys', 'json', 're', 'datetime', 'pathlib']:
                continue
            
            if file_type in ['js', 'jsx', 'ts', 'tsx'] and dep in ['fs', 'path', 'util', 'crypto']:
                continue
            
            filtered_deps.append(dep)
        
        return list(set(filtered_deps))  # Remove duplicates
    
    @staticmethod
    def extract_functions_and_classes(content: str, file_type: str) -> Dict[str, List[str]]:
        """Extract function and class names from code"""
        result = {'functions': [], 'classes': []}
        
        if file_type in ['js', 'jsx', 'ts', 'tsx']:
            # JavaScript/TypeScript functions and classes
            function_patterns = [
                r'function\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'const\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(?:\([^)]*\)|[^=])\s*=>',
                r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(?:\([^)]*\)|[^,}])\s*=>'
            ]
            
            class_patterns = [
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'interface\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                r'type\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*='
            ]
        
        elif file_type == 'py':
            # Python functions and classes
            function_patterns = [
                r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
                r'async\s+def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            ]
            
            class_patterns = [
                r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ]
        
        elif file_type == 'cs':
            # C# methods and classes
            function_patterns = [
                r'(?:public|private|protected|internal)?\s*(?:static\s+)?(?:async\s+)?[a-zA-Z<>\[\]]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
            ]
            
            class_patterns = [
                r'(?:public|private|protected|internal)?\s*(?:abstract\s+)?(?:class|interface|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)'
            ]
        
        else:
            return result
        
        # Extract functions
        for pattern in function_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            result['functions'].extend(matches)
        
        # Extract classes
        for pattern in class_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            result['classes'].extend(matches)
        
        # Remove duplicates and filter out common false positives
        result['functions'] = list(set(result['functions']))
        result['classes'] = list(set(result['classes']))
        
        return result
    
    @staticmethod
    def get_file_summary(file_path: str, content: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a file"""
        file_path = Path(file_path)
        file_type = file_path.suffix.lstrip('.').lower()
        
        summary = {
            'file_path': str(file_path),
            'file_type': file_type,
            'file_name': file_path.name,
            'size': len(content),
            'lines': len(content.split('\n')),
            'dependencies': [],
            'functions': [],
            'classes': [],
            'config_data': {}
        }
        
        # Parse specific file types
        if file_path.name == 'package.json':
            summary['config_data'] = FileParser.parse_package_json(content)
            summary['dependencies'] = list(summary['config_data'].get('dependencies', {}).keys())
        
        elif file_path.suffix == '.csproj':
            summary['config_data'] = FileParser.parse_csproj(content)
            summary['dependencies'] = list(summary['config_data'].get('package_references', {}).keys())
        
        elif file_path.name == 'requirements.txt':
            summary['config_data'] = FileParser.parse_requirements_txt(content)
            summary['dependencies'] = list(summary['config_data'].keys())
        
        elif file_path.name.lower() == 'dockerfile':
            summary['config_data'] = FileParser.parse_dockerfile(content)
        
        elif file_path.suffix in ['.yml', '.yaml']:
            summary['config_data'] = FileParser.parse_yaml_config(content)
        
        # Extract code elements for source files
        if file_type in ['js', 'jsx', 'ts', 'tsx', 'py', 'cs']:
            summary['dependencies'] = FileParser.extract_dependencies_from_code(content, file_type)
            code_elements = FileParser.extract_functions_and_classes(content, file_type)
            summary['functions'] = code_elements['functions']
            summary['classes'] = code_elements['classes']
        
        return summary
