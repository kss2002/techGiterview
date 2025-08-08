"""
기술 스택 정확 식별 테스트

TDD 방식으로 RepositoryAnalyzer가 package.json과 실제 파일 내용을 기반으로
정확한 기술 스택을 식별하는지 검증하는 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any
import json

# 테스트 대상 모듈
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

from app.agents.repository_analyzer import RepositoryAnalyzer


class TestTechStackAccuracy:
    """기술 스택 정확 식별 검증 테스트"""
    
    @pytest.fixture
    def analyzer(self):
        """RepositoryAnalyzer 인스턴스 생성"""
        return RepositoryAnalyzer()
    
    @pytest.fixture
    def mock_typescript_package_json(self):
        """TypeScript 프로젝트의 package.json"""
        return {
            "name": "business-app",
            "version": "1.0.0",
            "type": "module",
            "main": "dist/index.js",
            "scripts": {
                "build": "tsc",
                "start": "node dist/index.js",
                "dev": "ts-node-dev src/index.ts",
                "test": "jest"
            },
            "dependencies": {
                "express": "^4.18.2",
                "@types/express": "^4.17.17",
                "typescript": "^4.9.5",
                "ts-node": "^10.9.1"
            },
            "devDependencies": {
                "@types/node": "^18.15.0",
                "jest": "^29.5.0",
                "ts-node-dev": "^2.0.0"
            }
        }
    
    @pytest.fixture
    def mock_vue_package_json(self):
        """Vue.js 프로젝트의 package.json"""
        return {
            "name": "vue-app",
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "serve": "vue-cli-service serve",
                "build": "vue-cli-service build",
                "lint": "vue-cli-service lint"
            },
            "dependencies": {
                "core-js": "^3.8.3",
                "vue": "^3.2.13",
                "vue-router": "^4.0.3",
                "vuex": "^4.0.0"
            },
            "devDependencies": {
                "@vue/cli-plugin-babel": "~5.0.0",
                "@vue/cli-service": "~5.0.0"
            }
        }
    
    @pytest.fixture
    def mock_github_languages(self):
        """GitHub API에서 반환되는 언어 통계"""
        return {
            "TypeScript": 45230,
            "JavaScript": 12450,
            "CSS": 3200,
            "HTML": 1800
        }
    
    def test_identify_typescript_from_package_json(self, analyzer, mock_typescript_package_json):
        """테스트: package.json에서 TypeScript 기술 스택 정확 식별"""
        
        # Given: TypeScript 프로젝트의 package.json과 파일 정보
        files = [
            {
                "path": "package.json",
                "name": "package.json", 
                "type": "file",
                "content": json.dumps(mock_typescript_package_json),
                "importance": "high"
            },
            {
                "path": "src/index.ts",
                "name": "index.ts",
                "type": "file", 
                "content": "import express from 'express';\nconst app = express();",
                "importance": "medium"
            }
        ]
        
        languages = {"TypeScript": 45230, "JavaScript": 12450}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: TypeScript 관련 기술들이 정확히 식별되어야 함
        assert "typescript" in tech_stack, "TypeScript가 식별되지 않았습니다"
        assert "express" in tech_stack, "Express가 식별되지 않았습니다"
        assert "javascript" in tech_stack, "JavaScript가 식별되지 않았습니다"
        
        # TypeScript 점수가 가장 높아야 함
        assert tech_stack["typescript"] > 0.5, f"TypeScript 점수가 너무 낮음: {tech_stack['typescript']}"
        
        # Vue.js는 식별되지 않아야 함 
        assert "vue" not in tech_stack, f"Vue.js가 잘못 식별되었습니다: {tech_stack}"
    
    def test_identify_vue_from_package_json(self, analyzer, mock_vue_package_json):
        """테스트: package.json에서 Vue.js 기술 스택 정확 식별"""
        
        # Given: Vue.js 프로젝트의 package.json과 파일 정보
        files = [
            {
                "path": "package.json",
                "name": "package.json",
                "type": "file",
                "content": json.dumps(mock_vue_package_json),
                "importance": "high"
            },
            {
                "path": "src/App.vue",
                "name": "App.vue",
                "type": "file",
                "content": "<template><div>Hello Vue</div></template><script>export default {}</script>",
                "importance": "medium"
            }
        ]
        
        languages = {"JavaScript": 35000, "Vue": 15000, "CSS": 5000}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: Vue.js 관련 기술들이 정확히 식별되어야 함
        assert "vue" in tech_stack, "Vue.js가 식별되지 않았습니다"
        assert "javascript" in tech_stack, "JavaScript가 식별되지 않았습니다"
        
        # Vue.js 점수가 높아야 함
        assert tech_stack["vue"] > 0.3, f"Vue.js 점수가 너무 낮음: {tech_stack['vue']}"
        
        # TypeScript나 React는 식별되지 않아야 함
        assert "typescript" not in tech_stack, f"TypeScript가 잘못 식별되었습니다: {tech_stack}"
        assert "react" not in tech_stack, f"React가 잘못 식별되었습니다: {tech_stack}"
    
    def test_distinguish_between_similar_frameworks(self, analyzer):
        """테스트: 유사한 프레임워크들을 정확히 구분하는지 검증"""
        
        # Given: React와 Vue가 모두 언급되는 경우
        files = [
            {
                "path": "package.json",
                "name": "package.json",
                "type": "file",
                "content": json.dumps({
                    "name": "mixed-project",
                    "dependencies": {
                        "react": "^18.0.0",
                        "react-dom": "^18.0.0"
                    }
                }),
                "importance": "high"
            },
            {
                "path": "src/components/Button.jsx",
                "name": "Button.jsx", 
                "type": "file",
                "content": "import React from 'react';\nexport const Button = () => <button>Click</button>;",
                "importance": "medium"
            }
        ]
        
        languages = {"JavaScript": 40000, "TypeScript": 5000}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: React는 식별되고 Vue는 식별되지 않아야 함
        assert "react" in tech_stack, "React가 식별되지 않았습니다"
        assert tech_stack["react"] > 0.4, f"React 점수가 너무 낮음: {tech_stack['react']}"
        
        # Vue.js는 식별되지 않아야 함
        assert "vue" not in tech_stack, f"Vue.js가 잘못 식별되었습니다: {tech_stack}"
    
    def test_handle_monorepo_tech_stack(self, analyzer):
        """테스트: 모노레포에서 여러 기술 스택이 공존하는 경우 처리"""
        
        # Given: 여러 기술이 혼재된 모노레포
        files = [
            {
                "path": "apps/frontend/package.json",
                "name": "package.json",
                "type": "file",
                "content": json.dumps({
                    "dependencies": {"react": "^18.0.0", "typescript": "^4.9.0"}
                }),
                "importance": "high"
            },
            {
                "path": "apps/backend/package.json", 
                "name": "package.json",
                "type": "file",
                "content": json.dumps({
                    "dependencies": {"express": "^4.18.0", "typescript": "^4.9.0"}
                }),
                "importance": "high"
            },
            {
                "path": "apps/frontend/src/App.tsx",
                "name": "App.tsx",
                "type": "file",
                "content": "import React from 'react';\nconst App = () => <div>Hello</div>;",
                "importance": "medium"
            },
            {
                "path": "apps/backend/src/server.ts",
                "name": "server.ts", 
                "type": "file",
                "content": "import express from 'express';\nconst app = express();",
                "importance": "medium"
            }
        ]
        
        languages = {"TypeScript": 50000, "JavaScript": 20000}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: 모든 주요 기술들이 식별되어야 함
        expected_techs = ["typescript", "react", "express", "javascript"]
        for tech in expected_techs:
            assert tech in tech_stack, f"{tech}가 식별되지 않았습니다"
        
        # TypeScript가 가장 높은 점수를 가져야 함
        assert tech_stack["typescript"] > 0.5, f"TypeScript 점수: {tech_stack['typescript']}"
    
    def test_fallback_to_file_extensions(self, analyzer):
        """테스트: package.json이 없을 때 파일 확장자로 기술 스택 식별"""
        
        # Given: package.json 없이 파일 확장자만 있는 경우
        files = [
            {
                "path": "src/main.py",
                "name": "main.py",
                "type": "file",
                "content": "import flask\napp = flask.Flask(__name__)",
                "importance": "high"
            },
            {
                "path": "requirements.txt",
                "name": "requirements.txt", 
                "type": "file",
                "content": "flask==2.3.0\nrequests==2.31.0",
                "importance": "medium"
            }
        ]
        
        languages = {"Python": 15000}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: Python과 Flask가 식별되어야 함
        assert "python" in tech_stack, "Python이 식별되지 않았습니다"
        assert "flask" in tech_stack, "Flask가 식별되지 않았습니다"
        
        # JavaScript 기술들은 식별되지 않아야 함
        js_techs = ["react", "vue", "angular", "express"]
        for tech in js_techs:
            assert tech not in tech_stack, f"{tech}가 잘못 식별되었습니다"
    
    def test_tech_stack_confidence_scoring(self, analyzer):
        """테스트: 기술 스택 신뢰도 점수가 적절히 계산되는지 검증"""
        
        # Given: 명확한 기술 스택 시그널이 있는 프로젝트
        files = [
            {
                "path": "package.json",
                "name": "package.json",
                "type": "file", 
                "content": json.dumps({
                    "dependencies": {
                        "react": "^18.0.0",
                        "react-dom": "^18.0.0",
                        "@types/react": "^18.0.0",
                        "typescript": "^4.9.0"
                    }
                }),
                "importance": "high"
            }
        ]
        
        languages = {"TypeScript": 30000, "JavaScript": 10000}
        
        # When: 기술 스택 분석 실행
        tech_stack = asyncio.run(analyzer._identify_tech_stack(files, languages))
        
        # Then: 높은 신뢰도 점수 검증
        assert tech_stack["react"] > 0.6, f"React 신뢰도가 낮음: {tech_stack['react']}"
        assert tech_stack["typescript"] > 0.6, f"TypeScript 신뢰도가 낮음: {tech_stack['typescript']}"
        
        # 점수 합리성 검증 (0-1 범위)
        for tech, score in tech_stack.items():
            assert 0 <= score <= 1, f"{tech}의 점수가 범위를 벗어남: {score}"


if __name__ == "__main__":
    # 테스트 실행
    pytest.main([__file__, "-v"])