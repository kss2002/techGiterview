"""
동적 가중치 시스템 테스트

사용자 요구사항:
- 면접질문을 만들때마다 각각의 가중치가 랜덤적으로 미세하게 변해서 
  면접질문에 들어가는 파일들이 조금씩 다를 수 있게 해줘
- 더미/샘플/테스트 데이터를 포함하지 않는 범용적 알고리즘
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from app.services.file_importance_analyzer import SmartFileImportanceAnalyzer
from app.agents.enhanced_question_generator import EnhancedQuestionGenerator


class TestDynamicWeightsSystem:
    """동적 가중치 시스템 테스트"""
    
    def setup_method(self):
        """테스트 셋업"""
        self.analyzer = SmartFileImportanceAnalyzer()
        self.question_generator = EnhancedQuestionGenerator()
        
        # 테스트용 샘플 데이터
        self.sample_files = [
            "src/main.py",
            "src/controllers/user_controller.py", 
            "src/models/user.py",
            "src/utils/helpers.py",
            "test/test_user.py",  # 테스트 파일 (제외되어야 함)
            "dummy/sample_data.json",  # 더미 데이터 (제외되어야 함)
            "examples/demo.py",  # 샘플 파일 (제외되어야 함)
            "src/services/user_service.py"
        ]
    
    def test_generate_dynamic_weights_variability(self):
        """동적 가중치 생성의 변동성 테스트"""
        
        # 다른 시드로 10번 가중치 생성
        weight_sets = []
        for i in range(10):
            weights = self.analyzer.generate_dynamic_weights(f"session_{i}")
            weight_sets.append(weights)
        
        # 모든 가중치 세트가 다른지 확인
        for i, weights1 in enumerate(weight_sets):
            for j, weights2 in enumerate(weight_sets[i+1:], i+1):
                # 적어도 하나의 가중치는 달라야 함
                assert weights1 != weights2, f"가중치 세트 {i}와 {j}가 동일함"
        
        # 각 가중치가 적절한 범위 내에 있는지 확인
        for weights in weight_sets:
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.001, f"총 가중치가 1.0이 아님: {total_weight}"
            
            # 각 가중치가 기본값의 ±5% 범위 내에 있는지 확인
            for key, weight in weights.items():
                base_weight = self.analyzer.base_importance_weights[key]
                variation = abs(weight - base_weight) / base_weight
                assert variation <= 0.06, f"{key} 가중치 변동이 6%를 초과: {variation:.3f}"
    
    def test_seed_reproducibility(self):
        """시드 기반 재현 가능성 테스트"""
        
        seed = "test_session_123"
        
        # 같은 시드로 여러 번 생성
        weights1 = self.analyzer.generate_dynamic_weights(seed)
        weights2 = self.analyzer.generate_dynamic_weights(seed)
        weights3 = self.analyzer.generate_dynamic_weights(seed)
        
        # 모두 동일해야 함
        assert weights1 == weights2 == weights3, "같은 시드로 생성한 가중치가 다름"
    
    def test_is_excluded_file_dummy_samples(self):
        """더미/샘플 데이터 제외 테스트"""
        
        # 제외되어야 할 파일들
        excluded_files = [
            "dummy/data.json",
            "sample/config.yml", 
            "examples/demo.py",
            "test/unit_test.py",
            "tests/integration_test.py",
            "mock/fake_data.csv",
            "fixture/user_fixture.json",
            "template/email_template.html",
            "bootstrap.py",
            "seed_data.sql",
            "migration_001.sql",
            "init_db.py",
            "setup_dev.sh",
            "temp_file.tmp",
            "backup.bak",
            "debug.log",
            ".vscode/settings.json"
        ]
        
        for file_path in excluded_files:
            assert self.analyzer.is_excluded_file(file_path), f"{file_path}가 제외되지 않음"
        
        # 포함되어야 할 파일들
        included_files = [
            "src/main.py",
            "src/controllers/user_controller.py",
            "src/models/user.py", 
            "src/services/auth_service.py",
            "src/utils/validation.py",
            "config/app_config.py",
            "package.json",
            "requirements.txt",
            "Dockerfile"
        ]
        
        for file_path in included_files:
            assert not self.analyzer.is_excluded_file(file_path), f"{file_path}가 잘못 제외됨"
    
    def test_calculate_enhanced_importance_scores_with_exclusion(self):
        """제외 패턴이 적용된 중요도 점수 계산 테스트"""
        
        # 테스트 데이터 (더미/샘플 파일 포함)
        metadata_scores = {
            "src/main.py": 0.9,
            "src/models/user.py": 0.8,
            "test/test_user.py": 0.7,  # 제외되어야 함
            "dummy/sample.json": 0.6,  # 제외되어야 함
            "examples/demo.py": 0.5,   # 제외되어야 함
            "src/utils/helpers.py": 0.4
        }
        
        dependency_centrality = {k: v * 0.8 for k, v in metadata_scores.items()}
        churn_scores = {k: v * 0.6 for k, v in metadata_scores.items()}
        complexity_scores = {k: v * 0.4 for k, v in metadata_scores.items()}
        
        # 세션 ID와 함께 점수 계산
        session_id = "test_session_exclusion"
        importance_scores = self.analyzer.calculate_enhanced_importance_scores(
            metadata_scores=metadata_scores,
            dependency_centrality=dependency_centrality,
            churn_scores=churn_scores,
            complexity_scores=complexity_scores,
            session_id=session_id
        )
        
        # 제외된 파일들이 결과에 없는지 확인
        excluded_files = ["test/test_user.py", "dummy/sample.json", "examples/demo.py"]
        for excluded_file in excluded_files:
            assert excluded_file not in importance_scores, f"제외되어야 할 파일 {excluded_file}이 결과에 포함됨"
        
        # 포함된 파일들이 결과에 있는지 확인
        included_files = ["src/main.py", "src/models/user.py", "src/utils/helpers.py"]
        for included_file in included_files:
            assert included_file in importance_scores, f"포함되어야 할 파일 {included_file}이 결과에 없음"
            assert 0.0 <= importance_scores[included_file] <= 1.0, f"점수 범위 오류: {importance_scores[included_file]}"
    
    def test_weight_updates_affect_scores(self):
        """가중치 변경이 점수에 영향을 주는지 테스트"""
        
        # 테스트 데이터
        metadata_scores = {"src/main.py": 1.0}
        dependency_centrality = {"src/main.py": 0.8}
        churn_scores = {"src/main.py": 0.6}
        complexity_scores = {"src/main.py": 0.4}
        
        # 다른 세션으로 여러 번 계산
        scores_by_session = {}
        for i in range(10):
            session_id = f"test_session_{i}"
            scores = self.analyzer.calculate_enhanced_importance_scores(
                metadata_scores=metadata_scores,
                dependency_centrality=dependency_centrality,
                churn_scores=churn_scores,
                complexity_scores=complexity_scores,
                session_id=session_id
            )
            scores_by_session[session_id] = scores["src/main.py"]
        
        # 점수들이 다른지 확인 (적어도 일부는 달라야 함)
        unique_scores = set(scores_by_session.values())
        assert len(unique_scores) > 1, "동적 가중치가 점수에 영향을 주지 않음"
        
        # 모든 점수가 합리적인 범위 내에 있는지 확인
        for session_id, score in scores_by_session.items():
            assert 0.0 <= score <= 1.0, f"세션 {session_id}의 점수가 범위를 벗어남: {score}"
    
    @pytest.mark.asyncio
    async def test_question_generator_with_dynamic_weights(self):
        """질문 생성기에서 동적 가중치 적용 테스트"""
        
        # 모의 분석 데이터
        analysis_data = {
            "repo_url": "https://github.com/test/repo",
            "smart_file_analysis": {
                "critical_files": [
                    {
                        "file_path": "src/main.py",
                        "importance_score": 0.9,
                        "reasons": ["핵심 진입점"],
                        "metrics": {
                            "structural_importance": 0.9,
                            "dependency_centrality": 0.8,
                            "churn_risk": 0.3,
                            "complexity_score": 0.6
                        }
                    },
                    {
                        "file_path": "test/test_main.py",  # 제외되어야 함
                        "importance_score": 0.7,
                        "reasons": ["테스트 파일"],
                        "metrics": {
                            "structural_importance": 0.2,
                            "dependency_centrality": 0.1,
                            "churn_risk": 0.5,
                            "complexity_score": 0.4
                        }
                    },
                    {
                        "file_path": "src/models/user.py",
                        "importance_score": 0.8,
                        "reasons": ["핵심 모델"],
                        "metrics": {
                            "structural_importance": 0.8,
                            "dependency_centrality": 0.7,
                            "churn_risk": 0.4,
                            "complexity_score": 0.5
                        }
                    }
                ]
            },
            "file_contents": {},
            "tech_stack": {"python": 0.8, "fastapi": 0.6}
        }
        
        # 다른 세션으로 질문 생성
        results_by_session = {}
        for i in range(3):
            session_id = f"question_test_session_{i}"
            
            with patch.object(self.question_generator, '_generate_content_based_questions') as mock_generate:
                mock_generate.return_value = [
                    {
                        "question": f"테스트 질문 {i}",
                        "category": "code_analysis",
                        "difficulty": "medium"
                    }
                ]
                
                result = await self.question_generator.generate_enhanced_questions(
                    analysis_data=analysis_data,
                    question_count=3,
                    session_id=session_id
                )
                
                results_by_session[session_id] = result
        
        # 모든 결과가 성공했는지 확인
        for session_id, result in results_by_session.items():
            assert result["success"], f"세션 {session_id}에서 질문 생성 실패"
            assert "questions" in result, f"세션 {session_id}에 질문이 없음"
    
    def test_file_filtering_in_integration(self):
        """통합 과정에서 파일 필터링 테스트"""
        
        analysis_data = {
            "smart_file_analysis": {
                "critical_files": [
                    {"file_path": "src/main.py", "importance_score": 0.9},
                    {"file_path": "test/test_main.py", "importance_score": 0.7},  # 제외
                    {"file_path": "dummy/data.json", "importance_score": 0.6},    # 제외
                    {"file_path": "src/models/user.py", "importance_score": 0.8},
                    {"file_path": "examples/demo.py", "importance_score": 0.5}    # 제외
                ]
            },
            "tech_stack": {}
        }
        
        session_id = "integration_test_session"
        integration_result = self.question_generator.integrate_smart_file_analysis(
            analysis_data, session_id
        )
        
        # 필터링된 파일 경로들 추출
        filtered_paths = [f["file_path"] for f in integration_result["prioritized_files"]]
        
        # 포함되어야 할 파일들
        expected_included = ["src/main.py", "src/models/user.py"]
        for path in expected_included:
            assert path in filtered_paths, f"포함되어야 할 파일 {path}이 없음"
        
        # 제외되어야 할 파일들
        expected_excluded = ["test/test_main.py", "dummy/data.json", "examples/demo.py"]
        for path in expected_excluded:
            assert path not in filtered_paths, f"제외되어야 할 파일 {path}이 포함됨"
        
        # 중요도 순으로 정렬되었는지 확인
        scores = [f["importance_score"] for f in integration_result["prioritized_files"]]
        assert scores == sorted(scores, reverse=True), "파일들이 중요도 순으로 정렬되지 않음"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])