import re
import json
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from core.project_scanner import ProjectProfile, ProjectFile
import requests

@dataclass
class LibraryReference:
    """Represents a library reference in code"""
    library: str
    file_path: str
    line_number: int
    context: str
    reference_type: str  # 'import', 'using', 'require', etc.

@dataclass
class CompatibilityResult:
    """Represents compatibility check result"""
    library: str
    is_compatible: bool
    conflicts: List[str]
    warnings: List[str]
    recommendations: List[str]

@dataclass
class UpgradeRecommendation:
    """Represents an upgrade recommendation"""
    library: str
    current_version: str
    recommended_version: str
    reason: str
    breaking_changes: List[str]
    migration_steps: List[str]

class FunctionHandler:
    """Handles library management function calls"""
    
    def __init__(self):
        # Common import/using patterns for different languages
        self.import_patterns = {
            'javascript': [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'import\([\'"]([^\'"]+)[\'"]\)'
            ],
            'typescript': [
                r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
                r'import\([\'"]([^\'"]+)[\'"]\)'
            ],
            'csharp': [
                r'using\s+([^;]+);',
                r'<PackageReference\s+Include="([^"]+)"'
            ],
            'python': [
                r'from\s+([^\s]+)\s+import',
                r'import\s+([^\s]+)',
            ]
        }
        
        # Framework compatibility matrices
        self.compatibility_matrix = {
            'react': {
                '18': ['react-dom@18', 'react-router-dom@6', '@types/react@18'],
                '17': ['react-dom@17', 'react-router-dom@5', '@types/react@17'],
            },
            'vue': {
                '3': [
                    'vue-router@4', 'vuex@4', 'pinia@2', '@vue/cli@5', 'vite@4',
                    '@vue/test-utils@2', 'vue-tsc@1', '@vitejs/plugin-vue@4',
                    'axios@1', 'typescript@5', '@types/node@20'
                ],
                '2': [
                    'vue-router@3', 'vuex@3', '@vue/cli@4', 'vue-template-compiler@2',
                    '@vue/test-utils@1', 'axios@0', 'typescript@4', '@types/node@16'
                ],
            },
            'dotnet': {
                '8': ['Microsoft.AspNetCore.App@8', 'Microsoft.EntityFrameworkCore@8'],
                '6': ['Microsoft.AspNetCore.App@6', 'Microsoft.EntityFrameworkCore@6'],
            }
        }
        
        # Latest stable versions for common Vue.js libraries
        self.vue_latest_versions = {
            'vue': '3.3.8',
            'vue-router': '4.2.5',
            'vuex': '4.0.2',
            'pinia': '2.1.7',
            'vite': '4.5.0',
            '@vue/cli': '5.0.8',
            '@vue/cli-service': '5.0.8',
            '@vitejs/plugin-vue': '4.4.0',
            'vue-tsc': '1.8.22',
            '@vue/test-utils': '2.4.1',
            'vitest': '0.34.6',
            'axios': '1.6.0',
            'typescript': '5.2.2',
            '@types/node': '20.8.7',
            'eslint-plugin-vue': '9.17.0',
            '@vue/eslint-config-typescript': '12.0.0'
        }
    
    def find_library_references(self, project: ProjectProfile, library_name: str) -> List[LibraryReference]:
        """
        Find all references to a specific library in the project
        
        Args:
            project: Project profile to search in
            library_name: Name of the library to find
            
        Returns:
            List of library references
        """
        references = []
        
        for file in project.files:
            file_refs = self._find_references_in_file(file, library_name)
            references.extend(file_refs)
        
        return references
    
    def _find_references_in_file(self, file: ProjectFile, library_name: str) -> List[LibraryReference]:
        """Find library references in a single file"""
        references = []
        lines = file.content.split('\n')
        
        # Determine language based on file type
        language = self._get_language_from_file_type(file.file_type)
        patterns = self.import_patterns.get(language, [])
        
        for line_num, line in enumerate(lines, 1):
            for pattern in patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    imported_lib = match.group(1)
                    
                    # Check if this matches our target library
                    if self._is_library_match(imported_lib, library_name):
                        ref_type = self._get_reference_type(pattern)
                        
                        reference = LibraryReference(
                            library=imported_lib,
                            file_path=file.path,
                            line_number=line_num,
                            context=line.strip(),
                            reference_type=ref_type
                        )
                        references.append(reference)
        
        return references
    
    def check_compatibility(self, existing_dependencies: Dict[str, str], new_library: str) -> CompatibilityResult:
        """
        Check compatibility of a new library with existing dependencies
        
        Args:
            existing_dependencies: Dictionary of current dependencies
            new_library: Library to check compatibility for
            
        Returns:
            CompatibilityResult with compatibility information
        """
        conflicts = []
        warnings = []
        recommendations = []
        
        # Parse new library name and version
        lib_name, lib_version = self._parse_library_spec(new_library)
        
        # Check for direct conflicts
        if lib_name in existing_dependencies:
            existing_version = existing_dependencies[lib_name]
            if existing_version != lib_version and lib_version != 'latest':
                conflicts.append(f"Version conflict: {lib_name} {existing_version} vs {lib_version}")
        
        # Check for peer dependency conflicts
        peer_conflicts = self._check_peer_dependencies(lib_name, lib_version, existing_dependencies)
        conflicts.extend(peer_conflicts)
        
        # Check framework compatibility
        framework_warnings = self._check_framework_compatibility(lib_name, existing_dependencies)
        warnings.extend(framework_warnings)
        
        # Generate recommendations
        if conflicts:
            recommendations.append("Review version conflicts before installing")
        if not conflicts and not warnings:
            recommendations.append("Library appears compatible with current setup")
        
        return CompatibilityResult(
            library=new_library,
            is_compatible=len(conflicts) == 0,
            conflicts=conflicts,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def list_incompatible_libraries(self, project: ProjectProfile, target_framework_version: str) -> List[str]:
        """
        List libraries incompatible with target framework version
        
        Args:
            project: Project profile
            target_framework_version: Target framework version (e.g., "react@18")
            
        Returns:
            List of incompatible library names
        """
        incompatible = []
        framework, version = self._parse_framework_version(target_framework_version)
        
        if framework not in self.compatibility_matrix:
            return incompatible
        
        compatible_libs = self.compatibility_matrix[framework].get(version, [])
        
        for lib_name, lib_version in project.dependencies.items():
            # Check if library is known to be incompatible
            if not self._is_version_compatible(lib_name, lib_version, compatible_libs):
                incompatible.append(f"{lib_name}@{lib_version}")
        
        return incompatible
    
    def suggest_library_upgrades(self, project: ProjectProfile, target_framework_version: str) -> List[UpgradeRecommendation]:
        """
        Suggest library upgrades for framework migration
        
        Args:
            project: Project profile
            target_framework_version: Target framework version
            
        Returns:
            List of upgrade recommendations
        """
        recommendations = []
        framework, version = self._parse_framework_version(target_framework_version)
        
        if framework not in self.compatibility_matrix:
            return recommendations
        
        target_libs = self.compatibility_matrix[framework].get(version, [])
        
        for lib_name, current_version in project.dependencies.items():
            # Find recommended version for this library
            recommended = self._find_recommended_version(lib_name, target_libs)
            
            if recommended and recommended != current_version:
                breaking_changes = self._get_breaking_changes(lib_name, current_version, recommended)
                migration_steps = self._get_migration_steps(lib_name, current_version, recommended)
                
                upgrade = UpgradeRecommendation(
                    library=lib_name,
                    current_version=current_version,
                    recommended_version=recommended,
                    reason=f"Compatibility with {target_framework_version}",
                    breaking_changes=breaking_changes,
                    migration_steps=migration_steps
                )
                recommendations.append(upgrade)
        
        return recommendations
    
    def get_general_upgrade_recommendations(self, project: ProjectProfile) -> List[UpgradeRecommendation]:
        """
        Get general upgrade recommendations for current dependencies
        
        Args:
            project: Project profile
            
        Returns:
            List of general upgrade recommendations
        """
        recommendations = []
        
        # Check if this is a Vue.js project
        if project.framework.lower() == 'vue.js':
            for lib_name, current_version in project.dependencies.items():
                if lib_name in self.vue_latest_versions:
                    latest_version = self.vue_latest_versions[lib_name]
                    current_clean = self._clean_version(current_version)
                    
                    if current_clean != latest_version and self._is_version_older(current_clean, latest_version):
                        breaking_changes = self._get_vue_breaking_changes(lib_name, current_clean, latest_version)
                        migration_steps = self._get_vue_migration_steps(lib_name, current_clean, latest_version)
                        
                        upgrade = UpgradeRecommendation(
                            library=lib_name,
                            current_version=current_version,
                            recommended_version=latest_version,
                            reason=f"Update to latest stable version for better performance and security",
                            breaking_changes=breaking_changes,
                            migration_steps=migration_steps
                        )
                        recommendations.append(upgrade)
        
        return recommendations
    
    # Helper methods
    
    def _get_language_from_file_type(self, file_type: str) -> str:
        """Map file type to language"""
        mapping = {
            'js': 'javascript',
            'jsx': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'cs': 'csharp',
            'py': 'python'
        }
        return mapping.get(file_type, 'unknown')
    
    def _clean_version(self, version: str) -> str:
        """Clean version string by removing ^ ~ and other prefixes"""
        return version.lstrip('^~>=<').split('-')[0].split('+')[0]
    
    def _is_version_older(self, current: str, latest: str) -> bool:
        """Simple version comparison - checks if current is older than latest"""
        try:
            current_parts = [int(x) for x in current.split('.')]
            latest_parts = [int(x) for x in latest.split('.')]
            
            # Pad with zeros if needed
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            return current_parts < latest_parts
        except (ValueError, AttributeError):
            return False
    
    def _get_vue_breaking_changes(self, library: str, current: str, latest: str) -> List[str]:
        """Get Vue.js specific breaking changes for library upgrades"""
        vue_breaking_changes = {
            'vue': {
                '2->3': [
                    'Global API changed to app-specific API',
                    'v-model usage changes',
                    'Filters removed',
                    'Event API changes ($on, $off, $once removed)',
                    'Functional components syntax change'
                ]
            },
            'vue-router': {
                '3->4': [
                    'History mode API changed',
                    'Router constructor changes',
                    'Navigation guards signature updated',
                    'Route meta fields typing changes'
                ]
            },
            'vuex': {
                '3->4': [
                    'Installation method changed',
                    'TypeScript support improved',
                    'Module registration syntax updated'
                ]
            }
        }
        
        if library in vue_breaking_changes:
            current_major = current.split('.')[0] if '.' in current else current
            latest_major = latest.split('.')[0] if '.' in latest else latest
            change_key = f"{current_major}->{latest_major}"
            
            return vue_breaking_changes[library].get(change_key, [])
        
        return []
    
    def _get_vue_migration_steps(self, library: str, current: str, latest: str) -> List[str]:
        """Get Vue.js specific migration steps for library upgrades"""
        vue_migration_steps = {
            'vue': {
                '2->3': [
                    'Update package.json dependencies',
                    'Replace Vue.createApp() instead of new Vue()',
                    'Update v-model usage patterns',
                    'Remove or replace filter usage',
                    'Update functional component syntax',
                    'Test all components thoroughly'
                ]
            },
            'vue-router': {
                '3->4': [
                    'Update package.json dependencies',
                    'Update router initialization syntax',
                    'Update navigation guard function signatures',
                    'Test all routes and navigation'
                ]
            }
        }
        
        if library in vue_migration_steps:
            current_major = current.split('.')[0] if '.' in current else current
            latest_major = latest.split('.')[0] if '.' in latest else latest
            change_key = f"{current_major}->{latest_major}"
            
            return vue_migration_steps[library].get(change_key, [
                f'Update {library} from {current} to {latest}',
                'Review documentation for breaking changes',
                'Test your application thoroughly'
            ])
        
        return [
            f'Update {library} from {current} to {latest}',
            'Review changelog for any breaking changes',
            'Test functionality after upgrade'
        ]
    
    def _is_library_match(self, imported_lib: str, target_lib: str) -> bool:
        """Check if imported library matches target library"""
        # Handle scoped packages and submodules
        if imported_lib == target_lib:
            return True
        
        # Check if imported lib starts with target (for submodules)
        if imported_lib.startswith(target_lib + '/'):
            return True
        
        # Handle relative imports that might reference the library
        if target_lib in imported_lib:
            return True
        
        return False
    
    def _get_reference_type(self, pattern: str) -> str:
        """Determine reference type from regex pattern"""
        if 'import' in pattern:
            return 'import'
        elif 'require' in pattern:
            return 'require'
        elif 'using' in pattern:
            return 'using'
        elif 'PackageReference' in pattern:
            return 'package_reference'
        else:
            return 'unknown'
    
    def _parse_library_spec(self, library_spec: str) -> Tuple[str, str]:
        """Parse library specification into name and version"""
        if '@' in library_spec and not library_spec.startswith('@'):
            # Handle package@version format
            parts = library_spec.rsplit('@', 1)
            return parts[0], parts[1]
        elif '==' in library_spec:
            # Handle package==version format (Python)
            parts = library_spec.split('==')
            return parts[0], parts[1]
        else:
            return library_spec, 'latest'
    
    def _parse_framework_version(self, framework_version: str) -> Tuple[str, str]:
        """Parse framework version string"""
        if '@' in framework_version:
            return framework_version.split('@', 1)
        else:
            return framework_version, 'latest'
    
    def _check_peer_dependencies(self, lib_name: str, lib_version: str, existing_deps: Dict[str, str]) -> List[str]:
        """Check for peer dependency conflicts"""
        # This would typically query npm/nuget APIs for peer dependencies
        # For now, return common known conflicts
        conflicts = []
        
        known_conflicts = {
            'react-router-dom': {
                '6': ['react@18'],
                '5': ['react@17']
            }
        }
        
        if lib_name in known_conflicts:
            required_peers = known_conflicts[lib_name].get(lib_version, [])
            for peer in required_peers:
                peer_name, peer_version = self._parse_library_spec(peer)
                if peer_name in existing_deps:
                    existing_peer_version = existing_deps[peer_name]
                    if existing_peer_version != peer_version:
                        conflicts.append(f"Peer dependency conflict: {peer_name} requires {peer_version}, found {existing_peer_version}")
        
        return conflicts
    
    def _check_framework_compatibility(self, lib_name: str, existing_deps: Dict[str, str]) -> List[str]:
        """Check framework compatibility warnings"""
        warnings = []
        
        # Check React version compatibility
        if 'react' in existing_deps:
            react_version = existing_deps['react']
            if lib_name.startswith('@material-ui') and react_version.startswith('18'):
                warnings.append("@material-ui may have issues with React 18, consider upgrading to @mui/material")
        
        return warnings
    
    def _is_version_compatible(self, lib_name: str, lib_version: str, compatible_libs: List[str]) -> bool:
        """Check if library version is in compatible list"""
        lib_spec = f"{lib_name}@{lib_version}"
        return any(comp_lib.startswith(lib_name) for comp_lib in compatible_libs)
    
    def _find_recommended_version(self, lib_name: str, target_libs: List[str]) -> Optional[str]:
        """Find recommended version for library in target list"""
        for target_lib in target_libs:
            if target_lib.startswith(lib_name + '@'):
                return target_lib.split('@', 1)[1]
        return None
    
    def _get_breaking_changes(self, lib_name: str, current_version: str, target_version: str) -> List[str]:
        """Get known breaking changes between versions"""
        # This would typically query changelog APIs or databases
        # For now, return common known breaking changes
        breaking_changes = []
        
        known_changes = {
            'react-router-dom': {
                '5->6': [
                    'Switch component replaced with Routes',
                    'useHistory hook replaced with useNavigate',
                    'Exact prop removed from Route'
                ]
            }
        }
        
        version_key = f"{current_version}->{target_version}"
        if lib_name in known_changes and version_key in known_changes[lib_name]:
            breaking_changes = known_changes[lib_name][version_key]
        
        return breaking_changes
    
    def _get_migration_steps(self, lib_name: str, current_version: str, target_version: str) -> List[str]:
        """Get migration steps for version upgrade"""
        steps = [
            f"Update {lib_name} from {current_version} to {target_version}",
            "Review breaking changes documentation",
            "Update import statements if needed",
            "Test application thoroughly"
        ]
        
        return steps
