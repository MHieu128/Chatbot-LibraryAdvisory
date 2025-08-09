#!/usr/bin/env python3
"""
Migration script to transfer data from JSON to ChromaDB
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

def migrate_json_to_chromadb():
    """Main migration function"""
    print("🔄 Starting migration from JSON to ChromaDB...")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Import ChromaDB utilities
        from chromadb_utils import ChromaDBManager, initialize_chromadb
        
        print("✓ ChromaDB utilities imported successfully")
        
        # Load existing JSON data
        json_file = "library_database.json"
        if not os.path.exists(json_file):
            print(f"❌ JSON file not found: {json_file}")
            return False
            
        with open(json_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            
        print(f"✓ Loaded {len(json_data)} libraries from JSON")
        
        # Initialize ChromaDB manager
        print("Initializing ChromaDB manager...")
        manager = ChromaDBManager()
        print("✓ ChromaDB manager initialized")
        
        # Check if collections already have data
        stats = manager.get_collection_stats()
        if stats.get('libraries', 0) > 0:
            response = input(f"⚠️  ChromaDB already contains {stats['libraries']} libraries. Continue migration? (y/n): ")
            if response.lower() not in ['y', 'yes']:
                print("Migration cancelled.")
                return False
        
        # Convert JSON data to ChromaDB format
        print("Converting and migrating library data...")
        migrated_count = 0
        
        for lib_key, lib_info in json_data.items():
            try:
                # Create comprehensive text for embedding
                description_text = f"{lib_info['name']} is a {lib_info['category']} library for {lib_info['language']}. {lib_info['description']}"
                
                # Enhanced metadata
                metadata = {
                    "key": lib_key,
                    "name": lib_info['name'],
                    "category": lib_info['category'],
                    "language": lib_info['language'],
                    "description": lib_info['description'],
                    "license": lib_info['license'],
                    "popularity": lib_info['popularity'],
                    "alternatives": json.dumps(lib_info.get('alternatives', [])),
                    "migrated_from": "json",
                    "migration_timestamp": datetime.now().isoformat()
                }
                
                # Add to ChromaDB using the collections directly
                manager.collections[manager.LIBRARIES_COLLECTION].add(
                    ids=[lib_key],
                    documents=[description_text],
                    metadatas=[metadata]
                )
                migrated_count += 1
                print(f"  ✓ Migrated: {lib_info['name']}")
                success = True
                
                    
            except Exception as e:
                print(f"  ❌ Error migrating {lib_info['name']}: {e}")
                
        print(f"\n✅ Migration completed!")
        print(f"  • Libraries migrated: {migrated_count}/{len(json_data)}")
        
        # Add sample FAQs
        print("\nAdding sample FAQs...")
        sample_faqs = [
            {
                "id": "faq_1",
                "question": "What's the difference between React and Vue.js?",
                "answer": "React is a library focused on UI components with a larger ecosystem, while Vue.js is a progressive framework with gentler learning curve and built-in features.",
                "category": "Frontend Frameworks",
                "keywords": ["react", "vue", "comparison", "frontend"]
            },
            {
                "id": "faq_2", 
                "question": "Should I choose Django or Flask for my Python web project?",
                "answer": "Django is better for rapid development with batteries-included approach, while Flask offers more flexibility and is ideal for microservices and custom architectures.",
                "category": "Python Web Frameworks",
                "keywords": ["django", "flask", "python", "web", "framework"]
            },
            {
                "id": "faq_3",
                "question": "What are the licensing considerations for open source libraries?",
                "answer": "MIT and BSD licenses are very permissive for commercial use. GPL requires derivative works to be open source. Apache 2.0 provides patent protection. Always review specific license terms.",
                "category": "Licensing",
                "keywords": ["license", "mit", "gpl", "apache", "open source"]
            }
        ]
        
        faq_added = 0
        for faq in sample_faqs:
            content = f"Q: {faq['question']} A: {faq['answer']}"
            metadata = {
                "question": faq['question'],
                "answer": faq['answer'],
                "category": faq['category'],
                "keywords": json.dumps(faq['keywords']),
                "created_at": datetime.now().isoformat()
            }
            
            manager.collections[manager.FAQS_COLLECTION].add(
                ids=[faq['id']],
                documents=[content],
                metadatas=[metadata]
            )
            faq_added += 1
            print(f"  ✓ Added FAQ: {faq['question'][:50]}...")
                
        print(f"  • FAQs added: {faq_added}/{len(sample_faqs)}")
        
        # Display final statistics
        final_stats = manager.get_collection_stats()
        print(f"\n📊 Final ChromaDB Statistics:")
        print(f"  • Libraries: {final_stats.get('libraries', 0)}")
        print(f"  • FAQs: {final_stats.get('faqs', 0)}")
        print(f"  • User Queries: {final_stats.get('user_queries', 0)}")
        
        # Backup JSON file
        backup_file = f"library_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            import shutil
            shutil.copy2(json_file, backup_file)
            print(f"✓ JSON backup created: {backup_file}")
        except Exception as e:
            print(f"⚠️  Could not create backup: {e}")
            
        print("\n🎉 Migration completed successfully!")
        print("You can now use ChromaDB for semantic search and enhanced functionality.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure ChromaDB dependencies are installed: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
        return False

def test_migration():
    """Test the migrated data"""
    print("\n🧪 Testing migrated data...")
    
    try:
        from chromadb_utils import ChromaDBManager
        
        manager = ChromaDBManager()
        
        # Test library search
        print("Testing library search...")
        results = manager.search_libraries("javascript framework", n_results=3)
        print(f"✓ Found {len(results)} results for 'javascript framework'")
        
        # Test FAQ search
        print("Testing FAQ search...")
        faq_results = manager.search_faqs("react vs vue", n_results=2)
        print(f"✓ Found {len(faq_results)} FAQ results for 'react vs vue'")
        
        # Test similar libraries
        print("Testing similar library search...")
        similar = manager.find_similar_libraries("React", n_results=2)
        print(f"✓ Found {len(similar)} similar libraries to React")
        
        print("✅ All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main function"""
    print("=" * 60)
    print("📚 Library Advisory System - ChromaDB Migration")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        success = test_migration()
    else:
        success = migrate_json_to_chromadb()
        
        if success:
            # Ask if user wants to run tests
            response = input("\nWould you like to test the migrated data? (y/n): ")
            if response.lower() in ['y', 'yes']:
                test_migration()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())