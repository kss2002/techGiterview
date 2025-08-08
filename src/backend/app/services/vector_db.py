"""
Vector Database Service

ChromaDB를 활용한 벡터 저장소 서비스
코드 스니펫과 분석 결과를 벡터로 저장하고 검색하는 기능을 제공
"""

import chromadb
import uuid
from typing import List, Dict, Optional, Any
from chromadb.config import Settings
import hashlib
import json

from app.core.config import settings


class VectorDBService:
    """벡터 데이터베이스 서비스"""
    
    def __init__(self):
        # 컬렉션들
        self.code_collection = None
        self.analysis_collection = None
        self.client = None
        
        # ChromaDB 클라이언트 초기화
        try:
            self.client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
                settings=Settings(allow_reset=True)
            )
        except Exception as e:
            print(f"ChromaDB HttpClient 초기화 실패: {e}")
            try:
                self.client = chromadb.Client()
            except Exception as local_e:
                print(f"ChromaDB 로컬 클라이언트 초기화 실패: {local_e}")
                self.client = None
        
        self._initialize_collections()
    
    def _initialize_collections(self):
        """컬렉션 초기화"""
        if not self.client:
            print("ChromaDB 클라이언트가 초기화되지 않음")
            return
            
        try:
            # 코드 스니펫 컬렉션
            self.code_collection = self.client.get_or_create_collection(
                name="code_snippets",
                metadata={"hnsw:space": "cosine"}
            )
            
            # 분석 결과 컬렉션
            self.analysis_collection = self.client.get_or_create_collection(
                name="analysis_results",
                metadata={"hnsw:space": "cosine"}
            )
            
        except Exception as e:
            print(f"ChromaDB 컬렉션 초기화 실패: {e}")
            self.code_collection = None
            self.analysis_collection = None
    
    async def store_code_snippets(self, repo_url: str, files: List[Dict[str, Any]]) -> List[str]:
        """코드 스니펫을 벡터 DB에 저장"""
        
        if not self.code_collection:
            print("ChromaDB 연결 없음 - 스니펫 저장 건너뜀")
            return []
        
        stored_ids = []
        
        for file_info in files:
            file_path = file_info["path"]
            content = file_info.get("content", "")
            
            if not content or len(content.strip()) < 50:  # 너무 짧은 파일 제외
                continue
            
            # 함수/클래스 단위로 분할
            snippets = self._extract_code_snippets(content, file_path)
            
            for snippet in snippets:
                snippet_id = self._generate_snippet_id(repo_url, file_path, snippet["start_line"])
                
                # 중복 제거를 위한 검사
                if not self._snippet_exists(snippet_id):
                    # 메타데이터 준비
                    metadata = {
                        "repo_url": repo_url,
                        "file_path": file_path,
                        "snippet_type": snippet["type"],
                        "start_line": snippet["start_line"],
                        "end_line": snippet["end_line"],
                        "language": self._detect_language(file_path),
                        "complexity": snippet.get("complexity", 1.0)
                    }
                    
                    # 벡터 저장
                    self.code_collection.add(
                        documents=[snippet["content"]],
                        metadatas=[metadata],
                        ids=[snippet_id]
                    )
                    
                    stored_ids.append(snippet_id)
        
        return stored_ids
    
    async def store_analysis_result(self, repo_url: str, analysis_data: Dict[str, Any]) -> str:
        """분석 결과를 벡터 DB에 저장"""
        
        if not self.analysis_collection:
            print("ChromaDB 연결 없음 - 분석 결과 저장 건너뜀")
            return ""
        
        analysis_id = self._generate_analysis_id(repo_url)
        
        # 분석 결과를 문서로 변환
        analysis_text = self._format_analysis_for_storage(analysis_data)
        
        metadata = {
            "repo_url": repo_url,
            "analysis_type": "repository_analysis",
            "tech_stack": json.dumps(analysis_data.get("tech_stack", {})),
            "complexity_score": analysis_data.get("complexity_score", 0.0),
            "file_count": analysis_data.get("file_count", 0),
            "timestamp": analysis_data.get("timestamp", "")
        }
        
        # 기존 분석 결과가 있다면 업데이트
        try:
            self.analysis_collection.delete(ids=[analysis_id])
        except:
            pass
        
        self.analysis_collection.add(
            documents=[analysis_text],
            metadatas=[metadata],
            ids=[analysis_id]
        )
        
        return analysis_id
    
    async def search_similar_code(self, query: str, language: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """유사한 코드 스니펫 검색"""
        
        if not self.code_collection:
            print("ChromaDB 연결 없음 - 코드 검색 건너뜀")
            return []
        
        where_filter = {}
        if language:
            where_filter["language"] = language
        
        try:
            results = self.code_collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter if where_filter else None
            )
            
            return self._format_search_results(results)
            
        except Exception as e:
            print(f"코드 검색 오류: {e}")
            return []
    
    async def search_analysis_context(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """특정 저장소의 분석 컨텍스트 검색"""
        
        if not self.analysis_collection:
            print("ChromaDB 연결 없음 - 분석 컨텍스트 검색 건너뜀")
            return None
        
        try:
            results = self.analysis_collection.query(
                query_texts=[repo_url],
                n_results=1,
                where={"repo_url": repo_url}
            )
            
            if results["documents"] and len(results["documents"][0]) > 0:
                return {
                    "analysis_text": results["documents"][0][0],
                    "metadata": results["metadatas"][0][0]
                }
            
        except Exception as e:
            print(f"분석 컨텍스트 검색 오류: {e}")
        
        return None
    
    async def get_code_by_complexity(self, min_complexity: float = 2.0, max_complexity: float = 8.0, limit: int = 10) -> List[Dict[str, Any]]:
        """복잡도 범위에 따른 코드 스니펫 조회"""
        
        if not self.code_collection:
            print("ChromaDB 연결 없음 - 복잡도 기반 검색 건너뜀")
            return []
        
        try:
            # ChromaDB는 범위 쿼리가 제한적이므로 전체 조회 후 필터링
            results = self.code_collection.get()
            
            filtered_results = []
            for i, metadata in enumerate(results["metadatas"]):
                complexity = metadata.get("complexity", 1.0)
                if min_complexity <= complexity <= max_complexity:
                    filtered_results.append({
                        "id": results["ids"][i],
                        "content": results["documents"][i],
                        "metadata": metadata
                    })
                    
                    if len(filtered_results) >= limit:
                        break
            
            return filtered_results
            
        except Exception as e:
            print(f"복잡도 기반 검색 오류: {e}")
            return []
    
    def _extract_code_snippets(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """코드에서 함수/클래스 스니펫 추출"""
        
        snippets = []
        lines = content.split('\n')
        
        # 언어별 패턴
        if file_path.endswith('.py'):
            snippets.extend(self._extract_python_snippets(lines))
        elif file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            snippets.extend(self._extract_javascript_snippets(lines))
        elif file_path.endswith('.java'):
            snippets.extend(self._extract_java_snippets(lines))
        else:
            # 기본적으로 파일 전체를 하나의 스니펫으로 처리
            snippets.append({
                "content": content,
                "type": "file",
                "start_line": 1,
                "end_line": len(lines),
                "complexity": self._calculate_snippet_complexity(content)
            })
        
        return snippets
    
    def _extract_python_snippets(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Python 함수/클래스 추출"""
        
        snippets = []
        current_snippet = None
        indent_stack = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
            
            # 들여쓰기 계산
            indent = len(line) - len(line.lstrip())
            
            # 함수 또는 클래스 시작
            if stripped.startswith('def ') or stripped.startswith('class '):
                # 이전 스니펫 종료
                if current_snippet:
                    current_snippet["end_line"] = i - 1
                    current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
                    current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
                    snippets.append(current_snippet)
                
                # 새 스니펫 시작
                snippet_type = "class" if stripped.startswith('class ') else "function"
                current_snippet = {
                    "type": snippet_type,
                    "start_line": i,
                    "content": "",
                    "end_line": i
                }
                indent_stack = [indent]
            
            # 스니펫 내용 확장
            elif current_snippet and (not indent_stack or indent >= indent_stack[0]):
                current_snippet["end_line"] = i
        
        # 마지막 스니펫 처리
        if current_snippet:
            current_snippet["end_line"] = len(lines)
            current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
            current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
            snippets.append(current_snippet)
        
        return snippets
    
    def _extract_javascript_snippets(self, lines: List[str]) -> List[Dict[str, Any]]:
        """JavaScript/TypeScript 함수/클래스 추출"""
        
        snippets = []
        brace_count = 0
        current_snippet = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue
            
            # 함수 또는 클래스 시작 감지
            if any(pattern in stripped for pattern in ['function ', 'class ', '=>', 'const ', 'let ', 'var ']):
                if any(keyword in stripped for keyword in ['function', 'class', '=>']) or '=' in stripped:
                    if current_snippet and brace_count == 0:
                        # 이전 스니펫 종료
                        current_snippet["end_line"] = i - 1
                        current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
                        current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
                        snippets.append(current_snippet)
                    
                    # 새 스니펫 시작
                    snippet_type = "class" if "class " in stripped else "function"
                    current_snippet = {
                        "type": snippet_type,
                        "start_line": i,
                        "content": "",
                        "end_line": i
                    }
                    brace_count = 0
            
            # 중괄호 카운트
            if current_snippet:
                brace_count += stripped.count('{') - stripped.count('}')
                current_snippet["end_line"] = i
                
                # 스니펫 종료 조건
                if brace_count == 0 and '{' in line:
                    current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
                    current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
                    snippets.append(current_snippet)
                    current_snippet = None
        
        return snippets
    
    def _extract_java_snippets(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Java 메서드/클래스 추출"""
        
        snippets = []
        brace_count = 0
        current_snippet = None
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('//'):
                continue
            
            # 클래스 또는 메서드 시작
            if any(keyword in stripped for keyword in ['public class', 'class', 'public ', 'private ', 'protected ']):
                if ('(' in stripped and ')' in stripped) or 'class ' in stripped:
                    if current_snippet and brace_count == 0:
                        current_snippet["end_line"] = i - 1
                        current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
                        current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
                        snippets.append(current_snippet)
                    
                    snippet_type = "class" if "class " in stripped else "method"
                    current_snippet = {
                        "type": snippet_type,
                        "start_line": i,
                        "content": "",
                        "end_line": i
                    }
                    brace_count = 0
            
            if current_snippet:
                brace_count += stripped.count('{') - stripped.count('}')
                current_snippet["end_line"] = i
                
                if brace_count == 0 and '{' in line:
                    current_snippet["content"] = '\n'.join(lines[current_snippet["start_line"]-1:current_snippet["end_line"]])
                    current_snippet["complexity"] = self._calculate_snippet_complexity(current_snippet["content"])
                    snippets.append(current_snippet)
                    current_snippet = None
        
        return snippets
    
    def _calculate_snippet_complexity(self, content: str) -> float:
        """스니펫의 복잡도 계산"""
        
        complexity = 1.0
        
        # 조건문, 반복문 등의 복잡도 증가 요소
        complexity_patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
            r'\btry\b', r'\bcatch\b', r'\bswitch\b', r'\bcase\b'
        ]
        
        import re
        for pattern in complexity_patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            complexity += matches * 0.5
        
        # 중첩 레벨
        max_indent = 0
        for line in content.split('\n'):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 4)
        
        complexity += max_indent * 0.3
        
        return round(complexity, 2)
    
    def _generate_snippet_id(self, repo_url: str, file_path: str, start_line: int) -> str:
        """스니펫 ID 생성"""
        content = f"{repo_url}#{file_path}#{start_line}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_analysis_id(self, repo_url: str) -> str:
        """분석 결과 ID 생성"""
        return hashlib.md5(repo_url.encode()).hexdigest()
    
    def _snippet_exists(self, snippet_id: str) -> bool:
        """스니펫 존재 여부 확인"""
        try:
            result = self.code_collection.get(ids=[snippet_id])
            return len(result["ids"]) > 0
        except:
            return False
    
    def _detect_language(self, file_path: str) -> str:
        """파일 경로에서 언어 감지"""
        
        if file_path.endswith('.py'):
            return 'python'
        elif file_path.endswith(('.js', '.jsx')):
            return 'javascript'
        elif file_path.endswith(('.ts', '.tsx')):
            return 'typescript'
        elif file_path.endswith('.java'):
            return 'java'
        elif file_path.endswith('.go'):
            return 'go'
        elif file_path.endswith('.rs'):
            return 'rust'
        elif file_path.endswith('.php'):
            return 'php'
        else:
            return 'unknown'
    
    def _format_analysis_for_storage(self, analysis_data: Dict[str, Any]) -> str:
        """분석 데이터를 저장용 텍스트로 변환"""
        
        text_parts = []
        
        # 기본 정보
        if "repo_info" in analysis_data:
            repo_info = analysis_data["repo_info"]
            text_parts.append(f"Repository: {repo_info.get('name', '')}")
            text_parts.append(f"Description: {repo_info.get('description', '')}")
            text_parts.append(f"Language: {repo_info.get('language', '')}")
        
        # 기술 스택
        if "tech_stack" in analysis_data:
            tech_list = list(analysis_data["tech_stack"].keys())
            text_parts.append(f"Tech Stack: {', '.join(tech_list)}")
        
        # 복잡도
        if "complexity_score" in analysis_data:
            text_parts.append(f"Complexity Score: {analysis_data['complexity_score']}")
        
        # 요약
        if "analysis_summary" in analysis_data:
            text_parts.append(f"Summary: {analysis_data['analysis_summary']}")
        
        return "\n".join(text_parts)
    
    def _format_search_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """검색 결과 포맷팅"""
        
        formatted_results = []
        
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else 0.0
                })
        
        return formatted_results
    
    async def reset_collections(self):
        """컬렉션 초기화 (개발/테스트용)"""
        try:
            self.client.delete_collection("code_snippets")
            self.client.delete_collection("analysis_results")
            self._initialize_collections()
        except Exception as e:
            print(f"컬렉션 초기화 오류: {e}")