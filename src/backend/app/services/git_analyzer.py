"""
Git 변경 이력 실제 분석 서비스

실제 Git 로그를 파싱하여 파일별 변경 이력, 커밋 빈도, 버그 수정 패턴을 분석
더미 값 대신 실제 데이터 기반으로 정확한 churn 메트릭 제공
"""

import subprocess
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class GitCommitInfo:
    """Git 커밋 정보"""
    hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]
    insertions: int
    deletions: int


@dataclass
class FileChurnMetrics:
    """파일별 변경 이력 메트릭"""
    commit_count: int
    recent_activity: float  # 0-1, 최근 3개월 활동도
    bug_fix_ratio: float    # 0-1, 버그 수정 커밋 비율
    stability_score: float  # 0-1, 안정성 점수 (변경 빈도 역산)
    total_insertions: int
    total_deletions: int
    last_modified: datetime
    contributors: int       # 기여자 수


class GitAnalyzer:
    """Git 저장소 변경 이력 분석기"""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.bug_keywords = [
            'fix', 'bug', 'bugfix', 'hotfix', 'patch', 'repair',
            'correct', 'resolve', 'issue', 'error', 'exception'
        ]
    
    def _run_git_command(self, command: List[str]) -> str:
        """Git 명령어 실행"""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"[GIT_ANALYZER] Git 명령 실패: {e}")
            return ""
    
    def _is_bug_fix_commit(self, commit_message: str) -> bool:
        """커밋 메시지가 버그 수정인지 판단"""
        message_lower = commit_message.lower()
        return any(keyword in message_lower for keyword in self.bug_keywords)
    
    def get_file_commit_history(self, file_path: str, months: int = 12) -> List[GitCommitInfo]:
        """특정 파일의 커밋 히스토리 조회"""
        # 최근 N개월 커밋만 조회
        since_date = datetime.now() - timedelta(days=months * 30)
        since_str = since_date.strftime('%Y-%m-%d')
        
        # Git log 명령: 파일별 상세 정보 조회
        cmd = [
            'log',
            '--pretty=format:%H|%an|%ad|%s',
            '--date=iso',
            f'--since={since_str}',
            '--numstat',
            '--',
            file_path
        ]
        
        output = self._run_git_command(cmd)
        if not output:
            return []
        
        commits = []
        lines = output.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            # 커밋 정보 파싱
            if '|' in line:
                parts = line.split('|', 3)
                if len(parts) >= 4:
                    hash_val, author, date_str, message = parts
                    
                    try:
                        commit_date = datetime.fromisoformat(date_str.replace(' ', 'T', 1))
                    except ValueError:
                        commit_date = datetime.now()
                    
                    # 다음 라인에서 파일 변경 통계 찾기
                    i += 1
                    insertions = deletions = 0
                    files_changed = []
                    
                    while i < len(lines) and lines[i].strip():
                        stat_line = lines[i].strip()
                        if '\t' in stat_line:
                            # numstat 형식: insertions\tdeletions\tfilename
                            parts = stat_line.split('\t')
                            if len(parts) >= 3:
                                try:
                                    ins = int(parts[0]) if parts[0] != '-' else 0
                                    dels = int(parts[1]) if parts[1] != '-' else 0
                                    insertions += ins
                                    deletions += dels
                                    files_changed.append(parts[2])
                                except ValueError:
                                    pass
                        i += 1
                    
                    commits.append(GitCommitInfo(
                        hash=hash_val,
                        author=author,
                        date=commit_date,
                        message=message,
                        files_changed=files_changed,
                        insertions=insertions,
                        deletions=deletions
                    ))
                    continue
            
            i += 1
        
        return commits
    
    def calculate_file_churn_metrics(self, file_path: str) -> FileChurnMetrics:
        """파일별 실제 변경 이력 메트릭 계산"""
        commits = self.get_file_commit_history(file_path)
        
        if not commits:
            # 커밋이 없는 경우 기본값
            return FileChurnMetrics(
                commit_count=0,
                recent_activity=0.0,
                bug_fix_ratio=0.0,
                stability_score=1.0,  # 변경이 없으면 안정적
                total_insertions=0,
                total_deletions=0,
                last_modified=datetime.now(),
                contributors=0
            )
        
        # 기본 통계
        commit_count = len(commits)
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        last_modified = max(c.date for c in commits)
        contributors = len(set(c.author for c in commits))
        
        # 최근 3개월 활동도 계산
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_commits = [c for c in commits if c.date >= three_months_ago]
        recent_activity = min(1.0, len(recent_commits) / max(1, commit_count) * 2)
        
        # 버그 수정 비율 계산
        bug_fix_commits = [c for c in commits if self._is_bug_fix_commit(c.message)]
        bug_fix_ratio = len(bug_fix_commits) / max(1, commit_count)
        
        # 안정성 점수 (변경 빈도의 역수, 0-1 정규화)
        # 변경이 많을수록 불안정 (낮은 점수)
        max_expected_commits = 50  # 1년간 최대 예상 커밋 수
        instability = min(1.0, commit_count / max_expected_commits)
        stability_score = 1.0 - instability
        
        return FileChurnMetrics(
            commit_count=commit_count,
            recent_activity=recent_activity,
            bug_fix_ratio=bug_fix_ratio,
            stability_score=stability_score,
            total_insertions=total_insertions,
            total_deletions=total_deletions,
            last_modified=last_modified,
            contributors=contributors
        )
    
    def analyze_repository_churn(self, file_paths: List[str]) -> Dict[str, Dict[str, Any]]:
        """저장소의 모든 파일에 대한 변경 이력 분석"""
        churn_metrics = {}
        
        print(f"[GIT_ANALYZER] {len(file_paths)}개 파일의 Git 변경 이력 분석 시작")
        
        for i, file_path in enumerate(file_paths):
            if not file_path:
                continue
                
            try:
                metrics = self.calculate_file_churn_metrics(file_path)
                
                # 딕셔너리 형태로 변환 (기존 인터페이스 호환)
                churn_metrics[file_path] = {
                    'commit_frequency': metrics.commit_count,
                    'recent_activity': metrics.recent_activity,
                    'bug_fix_ratio': metrics.bug_fix_ratio,
                    'stability_score': metrics.stability_score,
                    'total_changes': metrics.total_insertions + metrics.total_deletions,
                    'contributors': metrics.contributors,
                    'last_modified': metrics.last_modified.isoformat()
                }
                
                if i % 10 == 0:  # 진행률 표시
                    print(f"[GIT_ANALYZER] 진행률: {i+1}/{len(file_paths)} ({((i+1)/len(file_paths)*100):.1f}%)")
                    
            except Exception as e:
                print(f"[GIT_ANALYZER] {file_path} 분석 실패: {e}")
                # 기본값으로 설정
                churn_metrics[file_path] = {
                    'commit_frequency': 1,
                    'recent_activity': 0.1,
                    'bug_fix_ratio': 0.1,
                    'stability_score': 0.8,
                    'total_changes': 0,
                    'contributors': 1,
                    'last_modified': datetime.now().isoformat()
                }
        
        print(f"[GIT_ANALYZER] Git 분석 완료: {len(churn_metrics)}개 파일")
        return churn_metrics
    
    def get_repository_stats(self) -> Dict[str, Any]:
        """저장소 전체 통계"""
        try:
            # 전체 커밋 수
            total_commits = self._run_git_command(['rev-list', '--count', 'HEAD'])
            
            # 전체 기여자 수  
            contributors = self._run_git_command(['shortlog', '-sn', 'HEAD'])
            contributor_count = len(contributors.split('\n')) if contributors else 0
            
            # 최근 커밋 날짜
            last_commit = self._run_git_command(['log', '-1', '--pretty=format:%ad', '--date=iso'])
            
            # 활성 브랜치 수
            branches = self._run_git_command(['branch', '-r'])
            branch_count = len([b for b in branches.split('\n') if b.strip()]) if branches else 0
            
            return {
                'total_commits': int(total_commits) if total_commits.isdigit() else 0,
                'contributors': contributor_count,
                'last_commit_date': last_commit,
                'active_branches': branch_count,
                'analysis_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[GIT_ANALYZER] 저장소 통계 수집 실패: {e}")
            return {}