#!/usr/bin/env python3
"""
Function Calling Demo
Demonstrates the NuGet and npm package checking capabilities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from library_advisory_bot import LibraryAdvisoryBot, Colors

def demo_package_checking():
    """Demonstrate package checking functionality"""
    print(f"{Colors.HEADER}🔍 Function Calling Demo - Package Registry Integration{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")
    
    # Initialize bot
    bot = LibraryAdvisoryBot()
    
    # Demo NuGet package checking
    print(f"{Colors.OKBLUE}📦 Checking NuGet Package: Newtonsoft.Json{Colors.ENDC}")
    nuget_result = bot.check_nuget_package("Newtonsoft.Json")
    print(f"{Colors.OKGREEN}Results:{Colors.ENDC}")
    
    if nuget_result['status'] == 'found':
        print(f"  ✅ Package: {nuget_result['package_name']}")
        print(f"  ✅ Latest Version: {nuget_result['latest_version']}")
        print(f"  ✅ Registry: {nuget_result['registry']}")
        print(f"  ✅ Versions Available: {nuget_result['versions_count']}")
        print(f"  ✅ URL: {nuget_result['registry_url']}")
        
        metadata = nuget_result.get('metadata', {})
        if metadata:
            print(f"  ✅ Description: {metadata.get('description', 'N/A')[:100]}...")
            print(f"  ✅ Authors: {metadata.get('authors', 'N/A')}")
            print(f"  ✅ License: {metadata.get('license', 'N/A')}")
    else:
        print(f"  ❌ Error: {nuget_result.get('error', 'Unknown error')}")
    
    print("\n" + "-"*60 + "\n")
    
    # Demo npm package checking
    print(f"{Colors.OKBLUE}📦 Checking npm Package: express{Colors.ENDC}")
    npm_result = bot.check_npm_package("express")
    print(f"{Colors.OKGREEN}Results:{Colors.ENDC}")
    
    if npm_result['status'] == 'found':
        print(f"  ✅ Package: {npm_result['package_name']}")
        print(f"  ✅ Latest Version: {npm_result['latest_version']}")
        print(f"  ✅ Registry: {npm_result['registry']}")
        print(f"  ✅ Versions Available: {npm_result['versions_count']}")
        print(f"  ✅ URL: {npm_result['registry_url']}")
        
        metadata = npm_result.get('metadata', {})
        if metadata:
            print(f"  ✅ Description: {metadata.get('description', 'N/A')[:100]}...")
            print(f"  ✅ Author: {metadata.get('author', 'N/A')}")
            print(f"  ✅ License: {metadata.get('license', 'N/A')}")
            print(f"  ✅ Weekly Downloads: {metadata.get('weekly_downloads', 'N/A')}")
            print(f"  ✅ Homepage: {metadata.get('homepage', 'N/A')}")
    else:
        print(f"  ❌ Error: {npm_result.get('error', 'Unknown error')}")
    
    print("\n" + "-"*60 + "\n")
    
    # Demo AI-enhanced analysis with function calling
    if bot.use_ai:
        print(f"{Colors.OKBLUE}🤖 AI-Enhanced Analysis with Function Calling{Colors.ENDC}")
        print(f"{Colors.WARNING}Note: This requires Azure OpenAI to be configured{Colors.ENDC}")
        
        # Test with a library that should trigger function calling
        test_queries = [
            "Analyze the React package",
            "Tell me about the Express.js package", 
            "Compare Newtonsoft.Json with System.Text.Json"
        ]
        
        for query in test_queries:
            print(f"\n{Colors.OKCYAN}Query: {query}{Colors.ENDC}")
            response = bot._call_azure_openai(query)
            if response:
                print(f"{Colors.OKGREEN}Response:{Colors.ENDC}")
                print(response[:300] + "..." if len(response) > 300 else response)
            else:
                print(f"{Colors.WARNING}No AI response (check Azure OpenAI configuration){Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}AI features not available - configure Azure OpenAI for enhanced analysis{Colors.ENDC}")

def demo_error_handling():
    """Demonstrate error handling for non-existent packages"""
    print(f"\n{Colors.HEADER}🚨 Error Handling Demo{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*30}{Colors.ENDC}\n")
    
    bot = LibraryAdvisoryBot()
    
    # Test with non-existent packages
    print(f"{Colors.OKBLUE}Testing non-existent NuGet package{Colors.ENDC}")
    result = bot.check_nuget_package("this-package-should-not-exist-12345")
    print(f"Status: {result['status']}")
    print(f"Error: {result.get('error', 'No error')}")
    
    print(f"\n{Colors.OKBLUE}Testing non-existent npm package{Colors.ENDC}")
    result = bot.check_npm_package("this-package-should-not-exist-12345")
    print(f"Status: {result['status']}")
    print(f"Error: {result.get('error', 'No error')}")

if __name__ == "__main__":
    try:
        demo_package_checking()
        demo_error_handling()
        
        print(f"\n{Colors.OKGREEN}✅ Demo completed successfully!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}The Library Advisory System now includes:{Colors.ENDC}")
        print(f"  • Real-time NuGet package checking")
        print(f"  • Real-time npm package checking") 
        print(f"  • AI-enhanced analysis with function calling")
        print(f"  • Comprehensive metadata extraction")
        print(f"  • Error handling and validation")
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Demo failed: {e}{Colors.ENDC}")
