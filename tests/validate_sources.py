#!/usr/bin/env python3
"""
Validate URLs in sources.py and generate a report of broken links.
"""

import sys
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
import json
import os

# Add parent directory to path to import sources
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sources import SOURCES

# Configure retry strategy
def create_session():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    retry = Retry(
        total=2,
        connect=2,
        backoff_factor=0.5,
        status_forcelist=[408, 429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def test_url(url, timeout=10):
    """Test a URL and return its status"""
    session = create_session()
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = session.head(
            url, 
            timeout=timeout, 
            headers=headers, 
            allow_redirects=True,
            verify=False  # Ignore SSL warnings
        )
        return {
            'url': url,
            'status': response.status_code,
            'working': response.status_code < 400,
            'error': None
        }
    except requests.exceptions.Timeout:
        return {'url': url, 'status': None, 'working': False, 'error': 'Timeout'}
    except requests.exceptions.SSLError as e:
        return {'url': url, 'status': None, 'working': False, 'error': f'SSL Error: {str(e)[:50]}'}
    except requests.exceptions.ConnectionError as e:
        return {'url': url, 'status': None, 'working': False, 'error': f'Connection Error: {str(e)[:50]}'}
    except Exception as e:
        return {'url': url, 'status': None, 'working': False, 'error': f'{type(e).__name__}: {str(e)[:50]}'}
    finally:
        session.close()

def validate_sources():
    """Validate all URLs in sources.py"""
    print("🔍 Validating sources...")
    results = []
    
    for source in SOURCES:
        source_name = source['name']
        
        # Test main URL
        if 'url' in source:
            url = source['url']
            print(f"  Testing {source_name}: {url}...", end=' ')
            result = test_url(url)
            result['source'] = source_name
            result['type'] = 'main'
            results.append(result)
            status_icon = '✅' if result['working'] else '❌'
            print(f"{status_icon} ({result.get('status', 'Error')})")
        
        # Test RSS feeds
        if 'feeds' in source:
            for i, feed in enumerate(source['feeds']):
                print(f"  Testing {source_name} (feed {i+1}): {feed}...", end=' ')
                result = test_url(feed)
                result['source'] = source_name
                result['type'] = 'feed'
                result['index'] = i
                results.append(result)
                status_icon = '✅' if result['working'] else '❌'
                print(f"{status_icon} ({result.get('status', 'Error')})")
        
        # Test fallbacks
        if 'fallbacks' in source:
            for i, fallback in enumerate(source['fallbacks']):
                print(f"  Testing {source_name} (fallback {i+1}): {fallback}...", end=' ')
                result = test_url(fallback)
                result['source'] = source_name
                result['type'] = 'fallback'
                result['index'] = i
                results.append(result)
                status_icon = '✅' if result['working'] else '❌'
                print(f"{status_icon} ({result.get('status', 'Error')})")
    
    return results

def generate_report(results):
    """Generate a validation report"""
    broken = [r for r in results if not r['working']]
    working = [r for r in results if r['working']]
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_urls': len(results),
        'working': len(working),
        'broken': len(broken),
        'broken_urls': broken
    }
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'url_validation_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Report saved to {report_path}")
    return report

def print_summary(report):
    """Print summary of validation results"""
    print("\n" + "="*60)
    print("📋 VALIDATION SUMMARY")
    print("="*60)
    print(f"Total URLs tested: {report['total_urls']}")
    print(f"✅ Working: {report['working']}")
    print(f"❌ Broken: {report['broken']}")
    
    if report['broken'] > 0:
        print("\n🔴 BROKEN URLS:")
        for item in report['broken_urls']:
            print(f"  - {item['source']} ({item['type']})")
            print(f"    URL: {item['url']}")
            print(f"    Error: {item.get('error', 'Unknown')}")
            print()
    
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("🚀 Starting URL Validation")
    print("="*60)
    print()
    
    results = validate_sources()
    report = generate_report(results)
    print_summary(report)
    
    # Exit with error code if broken URLs found
    sys.exit(1 if report['broken'] > 0 else 0)
