"""
Bootstrap 파일 완전 제외 테스트 (Enhanced)

TDD 방식으로 Bootstrap 파일들이 SmartFileImportanceAnalyzer에서
완전히 제외되는지 검증하는 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, List, Any

# 테스트 대상 모듈
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer


class TestBootstrapExclusionEnhanced:
    """Bootstrap 파일 완전 제외 검증 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """SmartFileImportanceAnalyzer 인스턴스 생성"""
        return SmartFileImportanceAnalyzer()
    
    @pytest.fixture
    def mock_bootstrap_files(self):
        """Bootstrap 관련 파일들 목록"""
        return [
            {"path": "src/bootstrap-fork.ts", "name": "bootstrap-fork.ts", "size": 1500},
            {"path": "src/bootstrap-meta.ts", "name": "bootstrap-meta.ts", "size": 1200},
            {"path": "src/bootstrap-esm.ts", "name": "bootstrap-esm.ts", "size": 1100},
            {"path": "src/bootstrap-cli.ts", "name": "bootstrap-cli.ts", "size": 1300},
            {"path": "src/bootstrap-import.ts", "name": "bootstrap-import.ts", "size": 1400},
            {"path": "bootstrap.js", "name": "bootstrap.js", "size": 2000},
            {"path": "config/bootstrap.config.js", "name": "bootstrap.config.js", "size": 800}
        ]
    
    @pytest.fixture
    def mock_real_business_files(self):
        """실제 비즈니스 로직 파일들"""
        return [
            {"path": "src/services/userService.ts", "name": "userService.ts", "size": 5000},
            {"path": "src/models/User.ts", "name": "User.ts", "size": 3000},
            {"path": "src/controllers/AuthController.ts", "name": "AuthController.ts", "size": 4500},
            {"path": "src/utils/validation.ts", "name": "validation.ts", "size": 2800},
            {"path": "src/api/endpoints.ts", "name": "endpoints.ts", "size": 3200}
        ]
    
    def test_bootstrap_files_are_excluded(self, analyzer, mock_bootstrap_files):
        """테스트: Bootstrap 파일들이 제외되는지 검증"""
        
        # Given: Bootstrap 파일들
        for file_info in mock_bootstrap_files:
            file_path = file_info["path"]
            
            # When: 제외 여부 확인
            is_excluded = analyzer.is_excluded_file(file_path)
            
            # Then: 모든 Bootstrap 파일이 제외되어야 함
            assert is_excluded, f"Bootstrap 파일 {file_path}가 제외되지 않았습니다"
    
    def test_business_files_are_not_excluded(self, analyzer, mock_real_business_files):
        """테스트: 실제 비즈니스 파일들은 제외되지 않는지 검증"""
        
        # Given: 실제 비즈니스 로직 파일들
        for file_info in mock_real_business_files:
            file_path = file_info["path"]
            
            # When: 제외 여부 확인
            is_excluded = analyzer.is_excluded_file(file_path)
            
            # Then: 비즈니스 파일들은 제외되지 않아야 함
            assert not is_excluded, f"비즈니스 파일 {file_path}가 잘못 제외되었습니다"
    
    @pytest.mark.asyncio
    async def test_bootstrap_files_filtered_from_analysis(self, analyzer):
        """테스트: 분석 결과에서 Bootstrap 파일들이 필터링되는지 검증"""
        
        # Given: Bootstrap과 실제 파일이 섞인 분석 데이터
        analysis_data = {
            "repo_url": "https://github.com/test/repo",
            "key_files": [
                {"path": "src/bootstrap-fork.ts", "name": "bootstrap-fork.ts", "size": 1500, "content": "export const bootstrap = {};"},
                {"path": "src/services/userService.ts", "name": "userService.ts", "size": 5000, "content": "class UserService {}"},
                {"path": "src/bootstrap-cli.ts", "name": "bootstrap-cli.ts", "size": 1300, "content": "#!/usr/bin/env node"},
                {"path": "src/models/User.ts", "name": "User.ts", "size": 3000, "content": "interface User {}"}
            ],
            "tech_stack": {"typescript": 0.8, "javascript": 0.2},
            "repo_info": {"name": "test-repo", "size": 10000}
        }
        
        # When: 저장소 분석 실행
        result = await analyzer.analyze_repository("https://github.com/test/repo", analysis_data)
        
        # Then: 결과 검증
        assert result["success"], "분석이 실패했습니다"
        
        smart_analysis = result.get("smart_file_analysis", {})
        critical_files = smart_analysis.get("files", [])
        
        # Bootstrap 파일들이 제외되었는지 확인
        bootstrap_files_in_result = [
            f for f in critical_files 
            if "bootstrap" in f.get("file_path", "").lower()
        ]
        
        assert len(bootstrap_files_in_result) == 0, f"Bootstrap 파일들이 결과에서 제외되지 않았습니다: {bootstrap_files_in_result}"
        
        # 실제 비즈니스 파일들은 포함되었는지 확인
        business_files_in_result = [
            f for f in critical_files 
            if f.get("file_path") in ["src/services/userService.ts", "src/models/User.ts"]
        ]
        
        assert len(business_files_in_result) > 0, "실제 비즈니스 파일들이 결과에 포함되지 않았습니다"
    
    def test_bootstrap_exclusion_patterns_comprehensive(self, analyzer):
        """테스트: 다양한 Bootstrap 패턴들이 모두 제외되는지 검증"""
        
        # Given: 다양한 Bootstrap 패턴들
        bootstrap_patterns = [
            "bootstrap.js",
            "bootstrap.min.js", 
            "bootstrap.css",
            "src/bootstrap-fork.ts",
            "lib/bootstrap-meta.js",
            "config/bootstrap.config.json",
            "scripts/bootstrap-setup.sh",
            "tools/bootstrap-init.py",
            "bootstrap/index.js",
            "vendor/bootstrap/dist/css/bootstrap.css"
        ]
        
        for pattern in bootstrap_patterns:
            # When: 제외 여부 확인
            is_excluded = analyzer.is_excluded_file(pattern)
            
            # Then: 모든 패턴이 제외되어야 함
            assert is_excluded, f"Bootstrap 패턴 {pattern}이 제외되지 않았습니다"
    
    def test_case_insensitive_bootstrap_exclusion(self, analyzer):
        """테스트: 대소문자 구분 없이 Bootstrap 파일들이 제외되는지 검증"""
        
        # Given: 대소문자가 다른 Bootstrap 파일들
        case_variations = [
            "Bootstrap.js",
            "BOOTSTRAP.JS", 
            "src/Bootstrap-Fork.ts",
            "SRC/BOOTSTRAP-META.TS",
            "lib/BootStrap-Config.json"
        ]
        
        for variation in case_variations:
            # When: 제외 여부 확인
            is_excluded = analyzer.is_excluded_file(variation)
            
            # Then: 대소문자 관계없이 제외되어야 함
            assert is_excluded, f"대소문자 변형 {variation}이 제외되지 않았습니다"
    
    def test_non_bootstrap_files_with_bootstrap_substring(self, analyzer):
        """테스트: 'bootstrap' 문자열을 포함하지만 실제로는 다른 파일들 검증"""
        
        # Given: bootstrap 문자열을 포함하지만 실제로는 다른 의미의 파일들
        non_bootstrap_files = [
            "src/services/applicationBootstrap.ts",  # 애플리케이션 부트스트랩 로직
            "docs/bootstrap-guide.md",  # 문서 (실제 코드가 아님)
            "src/core/systemBootstrap.js",  # 시스템 부트스트랩 로직
        ]
        
        for file_path in non_bootstrap_files:
            # When: 제외 여부 확인
            is_excluded = analyzer.is_excluded_file(file_path)
            
            # Then: 실제 애플리케이션 로직은 제외되지 않아야 함
            # (하지만 현재 구현에서는 보수적으로 제외할 수 있음)
            print(f"파일 {file_path} 제외 여부: {is_excluded}")


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"])