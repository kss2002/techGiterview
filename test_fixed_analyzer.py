#!/usr/bin/env python3
"""
Test script to verify the fixed SmartFileImportanceAnalyzer integration
"""

import requests
import json
import time

def test_django_repository_analysis():
    """Test Django repository analysis to ensure 12+ relevant files are selected"""
    # Django 프로젝트 URL (더 작은 Django 프로젝트로 테스트)
    test_repo_url = "https://github.com/django/django-contrib-comments"
    
    print(f"🔍 Testing SmartFileImportanceAnalyzer fix with Django repository")
    print(f"📂 Repository: {test_repo_url}")
    print("=" * 60)
    
    try:
        # GitHub 분석 API 호출
        api_url = "http://127.0.0.1:8002/api/v1/repository/analyze"
        payload = {
            "repo_url": test_repo_url
        }
        
        print(f"📡 Sending request to: {api_url}")
        print(f"📤 Payload: {json.dumps(payload, indent=2)}")
        
        start_time = time.time()
        response = requests.post(api_url, json=payload, timeout=120)  # 2분 타임아웃
        end_time = time.time()
        
        print(f"⏱️  Request completed in {end_time - start_time:.2f} seconds")
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Analysis successful!")
            
            # 결과 분석
            key_files = result.get("key_files", [])
            print(f"\n📋 Selected Files ({len(key_files)}):")
            print("-" * 40)
            
            for i, file_info in enumerate(key_files, 1):
                file_path = file_info.get("path", "unknown")
                file_size = file_info.get("size", 0)
                print(f"  {i:2d}. {file_path} ({file_size:,} bytes)")
            
            # 검증
            print(f"\n🔍 Analysis Results:")
            print(f"  - Total files selected: {len(key_files)}")
            
            # Django 관련 파일 확인
            django_files = [f for f in key_files if any(keyword in f.get("path", "").lower() 
                           for keyword in ["models", "views", "settings", "urls", "admin", "forms", "django"])]
            print(f"  - Django-related files: {len(django_files)}")
            
            # Dot 파일 확인
            dot_files = [f for f in key_files if f.get("path", "").startswith('.') or '/.' in f.get("path", "")]
            print(f"  - Dot files (should be 0): {len(dot_files)}")
            
            # 성공 여부 판단
            if len(key_files) >= 10:  # 적어도 10개 이상
                print(f"✅ SUCCESS: SmartFileImportanceAnalyzer selected {len(key_files)} files")
            else:
                print(f"❌ FAILURE: Only {len(key_files)} files selected (expected 12+)")
            
            if len(dot_files) == 0:
                print(f"✅ SUCCESS: Dot files properly excluded")
            else:
                print(f"❌ FAILURE: {len(dot_files)} dot files included: {[f.get('path') for f in dot_files]}")
            
            # 결과 summary
            print(f"\n📈 Quality Indicators:")
            diversity_score = len(set(f.get("path", "").split("/")[0] for f in key_files))
            print(f"  - Directory diversity: {diversity_score} different root directories")
            
        else:
            print(f"❌ Analysis failed!")
            print(f"📄 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_django_repository_analysis()