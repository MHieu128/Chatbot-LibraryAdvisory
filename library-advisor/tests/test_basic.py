import unittest
import tempfile
import shutil
import os
from pathlib import Path
import sys

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project_scanner import ProjectScanner
from core.embedding_manager import EmbeddingManager
from utils.validators import validate_project_structure, parse_version_string, compare_versions

class TestProjectScanner(unittest.TestCase):
    """Test cases for ProjectScanner"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.scanner = ProjectScanner(['.js', '.ts', '.json', '.py', '.cs'])
        
        # Create a sample project structure
        self.create_sample_project()
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)
    
    def create_sample_project(self):
        """Create a sample project for testing"""
        project_dir = Path(self.temp_dir) / "test_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": "test-project",
            "version": "1.0.0",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0"
            },
            "devDependencies": {
                "@types/react": "^18.0.0"
            }
        }
        
        with open(project_dir / "package.json", "w") as f:
            import json
            json.dump(package_json, f)
        
        # Create some JavaScript files
        with open(project_dir / "index.js", "w") as f:
            f.write("""
import React from 'react';
import ReactDOM from 'react-dom';

function App() {
    return <h1>Hello World</h1>;
}

ReactDOM.render(<App />, document.getElementById('root'));
""")
        
        # Create TypeScript file
        src_dir = project_dir / "src"
        src_dir.mkdir(exist_ok=True)
        
        with open(src_dir / "component.tsx", "w") as f:
            f.write("""
import React from 'react';

interface Props {
    title: string;
}

export const Component: React.FC<Props> = ({ title }) => {
    return <div>{title}</div>;
};
""")
    
    def test_scan_project_directory(self):
        """Test scanning a project directory"""
        project_path = Path(self.temp_dir) / "test_project"
        profile = self.scanner.scan_project_directory(str(project_path))
        
        self.assertEqual(profile.name, "test_project")
        self.assertEqual(profile.framework, "React")
        self.assertIn("JavaScript", profile.languages)
        self.assertIn("TypeScript (React)", profile.languages)
        self.assertGreater(profile.total_files, 0)
        self.assertIn("react", profile.dependencies)
        self.assertIn("react-dom", profile.dependencies)
    
    def test_detect_framework(self):
        """Test framework detection"""
        project_path = Path(self.temp_dir) / "test_project"
        profile = self.scanner.scan_project_directory(str(project_path))
        
        self.assertEqual(profile.framework, "React")

class TestValidators(unittest.TestCase):
    """Test cases for validation utilities"""
    
    def test_parse_version_string(self):
        """Test version string parsing"""
        # Test basic versions
        v1 = parse_version_string("1.2.3")
        self.assertEqual(v1, {'major': 1, 'minor': 2, 'patch': 3})
        
        # Test versions with prefixes
        v2 = parse_version_string("^18.2.0")
        self.assertEqual(v2, {'major': 18, 'minor': 2, 'patch': 0})
        
        # Test partial versions
        v3 = parse_version_string("3.1")
        self.assertEqual(v3, {'major': 3, 'minor': 1, 'patch': 0})
    
    def test_compare_versions(self):
        """Test version comparison"""
        self.assertEqual(compare_versions("1.0.0", "1.0.0"), 0)  # Equal
        self.assertEqual(compare_versions("1.0.0", "1.0.1"), -1)  # First is smaller
        self.assertEqual(compare_versions("1.1.0", "1.0.9"), 1)   # First is larger
    
    def test_validate_project_structure(self):
        """Test project structure validation"""
        # Test non-existent path
        result = validate_project_structure("/non/existent/path")
        self.assertFalse(result['valid'])
        self.assertIn("does not exist", result['issues'][0])

class TestEmbeddingManager(unittest.TestCase):
    """Test cases for EmbeddingManager (mock tests)"""
    
    def test_embedding_document_creation(self):
        """Test EmbeddingDocument creation"""
        from core.embedding_manager import EmbeddingDocument
        
        doc = EmbeddingDocument(
            id="test_doc",
            content="Test content",
            metadata={"file_path": "test.js", "file_type": "js"}
        )
        
        self.assertEqual(doc.id, "test_doc")
        self.assertEqual(doc.content, "Test content")
        self.assertEqual(doc.metadata["file_type"], "js")

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
