"""
Git 변경 이력(Churn) 분석 시스템

GitHub API를 통한 파일별 변경 빈도, 작성자 수, 최근 활동도 분석
NetworkX와 같은 고급 분석 도구는 사용하지 않고 순수 통계 기반으로 동작
"""

import re
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
import statistics

from app.services.github_client import GitHubClient


class ActivityPeriod(Enum):
    """분석 기간 옵션"""
    ONE_MONTH = 30
    THREE_MONTHS = 90
    SIX_MONTHS = 180
    ONE_YEAR = 365


@dataclass
class CommitInfo:
    """커밋 정보"""
    sha: str
    author: str
    date: datetime
    message: str
    files_changed: List[str]
    additions: int
    deletions: int


@dataclass
class FileChurnMetrics:
    """파일별 churn 메트릭"""
    file_path: str
    commit_count: int
    author_count: int
    total_additions: int
    total_deletions: int
    last_modified: datetime
    activity_score: float
    hotspot_score: float


@dataclass
class ChurnAnalysisResult:
    """churn 분석 결과"""
    total_commits: int
    unique_authors: int
    file_metrics: Dict[str, FileChurnMetrics]
    hotspot_files: List[str]
    analysis_period: ActivityPeriod
    analyzed_at: datetime


class ChurnAnalyzer:
    """Git 변경 이력 분석기 (새로운 구현)"""
    
    def __init__(self):
        self.github_token = None  # GitHub API 토큰
        
    async def analyze_repository_churn(
        self, 
        owner: str, 
        repo: str, 
        period: ActivityPeriod = ActivityPeriod.SIX_MONTHS
    ) -> ChurnAnalysisResult:
        """저장소의 churn 분석 수행"""
        
        # 모든 커밋 데이터 수집
        all_commits = await self._fetch_all_commits(owner, repo, period)
        
        # 커밋 데이터 파싱
        parsed_commits = self._parse_commit_data(all_commits)
        
        # 파일별 churn 메트릭 계산
        file_metrics = self._calculate_file_churn_metrics(parsed_commits)
        
        # 핫스팟 파일 식별
        hotspot_files = self._identify_hotspot_files(file_metrics)
        
        # 결과 구성
        unique_authors = len(set(commit.author for commit in parsed_commits))
        
        return ChurnAnalysisResult(
            total_commits=len(parsed_commits),
            unique_authors=unique_authors,
            file_metrics=file_metrics,
            hotspot_files=[f.file_path for f in hotspot_files],
            analysis_period=period,
            analyzed_at=datetime.now()
        )
    
    async def _fetch_all_commits(
        self, 
        owner: str, 
        repo: str, 
        period: ActivityPeriod = ActivityPeriod.SIX_MONTHS
    ) -> List[Dict[str, Any]]:
        """모든 커밋 데이터를 페이지네이션으로 수집"""
        
        all_commits = []
        page = 1
        per_page = 100
        
        # 기간 설정
        since_date = datetime.now() - timedelta(days=period.value)
        
        while True:
            commits = await self._fetch_commit_history(
                owner, repo, since_date, page, per_page
            )
            
            if not commits:
                break
                
            all_commits.extend(commits)
            page += 1
            
            # 안전 장치: 최대 페이지 수 제한
            if page > 50:  # 최대 5000개 커밋
                break
        
        return all_commits
    
    async def _fetch_commit_history(
        self, 
        owner: str, 
        repo: str, 
        since: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """GitHub API로 커밋 히스토리 조회"""
        
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {
            "page": page,
            "per_page": per_page
        }
        
        if since:
            params["since"] = since.isoformat()
        
        return await self._make_github_request(url, params)
    
    async def _make_github_request(self, url: str, params: Dict = None) -> List[Dict[str, Any]]:
        """GitHub API 요청 실행"""
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ChurnAnalyzer/1.0"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # 각 커밋에 대해 파일 변경 정보 추가
                    for commit in data:
                        if "files" not in commit:
                            # 개별 커밋 세부 정보 조회
                            commit_detail = await self._fetch_commit_details(
                                commit["url"], session
                            )
                            if commit_detail:
                                commit.update(commit_detail)
                    
                    return data
                else:
                    raise Exception(f"GitHub API error: {response.status}")
    
    async def _fetch_commit_details(self, commit_url: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """개별 커밋의 세부 정보 조회"""
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ChurnAnalyzer/1.0"
        }
        
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        
        try:
            async with session.get(commit_url, headers=headers) as response:
                if response.status == 200:
                    detail = await response.json()
                    return {
                        "files": detail.get("files", []),
                        "stats": detail.get("stats", {"total": 0, "additions": 0, "deletions": 0})
                    }
        except Exception:
            pass
        
        return {}
    
    def _parse_commit_data(self, raw_commits: List[Dict[str, Any]]) -> List[CommitInfo]:
        """GitHub API 응답을 CommitInfo 객체로 파싱"""
        
        parsed_commits = []
        
        for commit_data in raw_commits:
            try:
                # 필수 필드 검증
                if "commit" not in commit_data or "author" not in commit_data["commit"]:
                    continue
                
                commit_info = commit_data["commit"]
                author_info = commit_info["author"]
                
                # 날짜 파싱
                date_str = author_info["date"]
                if date_str.endswith('Z'):
                    date_str = date_str[:-1] + '+00:00'
                commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                
                # 파일 변경 정보 추출
                files_changed = []
                total_additions = 0
                total_deletions = 0
                
                files = commit_data.get("files", [])
                for file_info in files:
                    files_changed.append(file_info["filename"])
                    total_additions += file_info.get("additions", 0)
                    total_deletions += file_info.get("deletions", 0)
                
                # stats 정보가 있으면 사용
                stats = commit_data.get("stats", {})
                if stats:
                    total_additions = stats.get("additions", total_additions)
                    total_deletions = stats.get("deletions", total_deletions)
                
                commit = CommitInfo(
                    sha=commit_data["sha"],
                    author=author_info["name"],
                    date=commit_date,
                    message=commit_info["message"],
                    files_changed=files_changed,
                    additions=total_additions,
                    deletions=total_deletions
                )
                
                parsed_commits.append(commit)
                
            except (KeyError, ValueError, TypeError):
                # 파싱 실패한 커밋은 건너뛰기
                continue
        
        return parsed_commits
    
    def _calculate_file_churn_metrics(self, commits: List[CommitInfo]) -> Dict[str, FileChurnMetrics]:
        """파일별 churn 메트릭 계산"""
        
        file_stats = defaultdict(lambda: {
            "commits": [],
            "authors": set(),
            "total_additions": 0,
            "total_deletions": 0,
            "last_modified": None
        })
        
        # 파일별 통계 수집
        for commit in commits:
            # 각 커밋의 파일 변경 정보를 파일별로 분배
            files_in_commit = len(commit.files_changed)
            if files_in_commit == 0:
                continue
            
            for file_path in commit.files_changed:
                stats = file_stats[file_path]
                stats["commits"].append(commit)
                stats["authors"].add(commit.author)
                
                # 파일별 변경량을 커밋의 총 변경량에서 균등 분배
                if files_in_commit == 1:
                    # 하나의 파일만 변경된 경우 전체 변경량 할당
                    stats["total_additions"] += commit.additions
                    stats["total_deletions"] += commit.deletions
                else:
                    # 여러 파일이 변경된 경우 균등 분배
                    stats["total_additions"] += commit.additions / files_in_commit
                    stats["total_deletions"] += commit.deletions / files_in_commit
                
                if stats["last_modified"] is None or commit.date > stats["last_modified"]:
                    stats["last_modified"] = commit.date
        
        # FileChurnMetrics 객체 생성
        file_metrics = {}
        for file_path, stats in file_stats.items():
            activity_score = self._calculate_activity_score(
                stats["last_modified"], 
                len(stats["commits"])
            )
            
            hotspot_score = self._calculate_hotspot_score(
                len(stats["commits"]),
                len(stats["authors"]),
                int(stats["total_additions"] + stats["total_deletions"])
            )
            
            metrics = FileChurnMetrics(
                file_path=file_path,
                commit_count=len(stats["commits"]),
                author_count=len(stats["authors"]),
                total_additions=int(stats["total_additions"]),
                total_deletions=int(stats["total_deletions"]),
                last_modified=stats["last_modified"],
                activity_score=activity_score,
                hotspot_score=hotspot_score
            )
            
            file_metrics[file_path] = metrics
        
        return file_metrics
    
    def _calculate_activity_score(self, last_modified: datetime, commit_count: int) -> float:
        """활동도 점수 계산 (0-1 범위)"""
        
        if last_modified is None:
            return 0.0
        
        # 날짜 타임존 처리
        now = datetime.now()
        if last_modified.tzinfo is not None:
            # last_modified가 timezone-aware면 now도 UTC로 맞춤
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if last_modified.tzinfo != timezone.utc:
                last_modified = last_modified.astimezone(timezone.utc)
        
        # 최근성 점수 (최근 30일 = 1.0, 1년 = 0.0)
        days_ago = (now - last_modified).days
        recency_score = max(0.0, 1.0 - (days_ago / 365.0))
        
        # 빈도 점수 (많은 커밋 = 높은 점수)
        frequency_score = min(1.0, commit_count / 20.0)
        
        # 가중 평균
        activity_score = (recency_score * 0.7) + (frequency_score * 0.3)
        
        return min(1.0, max(0.0, activity_score))
    
    def _calculate_hotspot_score(self, commit_count: int, author_count: int, total_changes: int) -> float:
        """핫스팟 점수 계산 (0-1 범위)"""
        
        # 커밋 빈도 점수
        frequency_score = min(1.0, commit_count / 50.0)
        
        # 작성자 다양성 점수 (많은 작성자 = 높은 점수)
        diversity_score = min(1.0, author_count / 10.0)
        
        # 변경 크기 점수
        size_score = min(1.0, total_changes / 1000.0)
        
        # 가중 평균
        hotspot_score = (frequency_score * 0.5) + (diversity_score * 0.3) + (size_score * 0.2)
        
        return min(1.0, max(0.0, hotspot_score))
    
    def _filter_commits_by_period(self, commits: List[CommitInfo], period: ActivityPeriod) -> List[CommitInfo]:
        """기간별 커밋 필터링"""
        
        cutoff_date = datetime.now() - timedelta(days=period.value)
        return [commit for commit in commits if commit.date > cutoff_date]
    
    def _identify_hotspot_files(
        self, 
        file_metrics: Dict[str, FileChurnMetrics], 
        threshold: float = 0.6
    ) -> List[FileChurnMetrics]:
        """핫스팟 파일 식별"""
        
        hotspots = [
            metrics for metrics in file_metrics.values()
            if metrics.hotspot_score > threshold
        ]
        
        # 핫스팟 점수 순으로 정렬
        hotspots.sort(key=lambda x: x.hotspot_score, reverse=True)
        
        return hotspots
    
    def _calculate_weighted_churn_score(self, metrics: FileChurnMetrics) -> float:
        """가중치 적용된 churn 점수 계산"""
        
        # 각 요소별 가중치
        weights = {
            "commit_frequency": 0.3,
            "activity": 0.3,
            "author_diversity": 0.2,
            "change_volume": 0.2
        }
        
        # 정규화된 점수들
        commit_score = min(1.0, metrics.commit_count / 20.0)
        activity_score = metrics.activity_score
        author_score = min(1.0, metrics.author_count / 5.0)
        volume_score = min(1.0, (metrics.total_additions + metrics.total_deletions) / 500.0)
        
        # 가중 평균
        weighted_score = (
            commit_score * weights["commit_frequency"] +
            activity_score * weights["activity"] +
            author_score * weights["author_diversity"] +
            volume_score * weights["change_volume"]
        )
        
        return min(1.0, max(0.0, weighted_score))
    
    def _detect_churn_patterns(self, commits: List[CommitInfo]) -> Dict[str, Any]:
        """변경 패턴 감지"""
        
        if not commits:
            return {}
        
        # 요일별 활동 분석
        weekday_commits = defaultdict(int)
        author_commits = defaultdict(int)
        total_changes = []
        
        for commit in commits:
            weekday_commits[commit.date.strftime("%A")] += 1
            author_commits[commit.author] += 1
            total_changes.append(commit.additions + commit.deletions)
        
        # 가장 활발한 요일과 작성자
        peak_day = max(weekday_commits.items(), key=lambda x: x[1])[0]
        most_active_author = max(author_commits.items(), key=lambda x: x[1])[0]
        
        # 평균 변경량
        avg_changes = statistics.mean(total_changes) if total_changes else 0
        
        return {
            "peak_activity_day": peak_day,
            "most_active_author": most_active_author,
            "average_changes_per_commit": round(avg_changes, 2),
            "commit_frequency_trend": "increasing"  # 간단한 구현
        }


class RuleBasedChurnAnalyzer:
    """순수 규칙 기반 Git 변경 이력 분석기"""
    
    def __init__(self):
        self.github_client = GitHubClient()
        
        # 버그 수정 키워드 패턴
        self.bug_fix_patterns = [
            r'\b(fix|fixes|fixed|fixing)\b',
            r'\b(bug|bugs)\b',
            r'\b(hotfix|hot-fix)\b',
            r'\b(patch|patches)\b',
            r'\b(issue|issues)\b',
            r'\b(problem|problems)\b'
        ]
        
        # 리팩토링 키워드 패턴
        self.refactor_patterns = [
            r'\b(refactor|refactoring|refactored)\b',
            r'\b(cleanup|clean-up|clean up)\b',
            r'\b(restructure|restructuring)\b',
            r'\b(reorganize|reorganizing)\b',
            r'\b(improve|improvement|improvements)\b',
            r'\b(optimize|optimization|optimizing)\b'
        ]
        
        # 핫스팟 임계값
        self.hotspot_thresholds = {
            "commit_frequency_percentile": 0.8,  # 상위 20%
            "recent_activity_threshold": 0.5,    # 50% 이상
            "change_intensity_percentile": 0.7   # 상위 30%
        }
        
        # 안정성 임계값
        self.stability_thresholds = {
            "commit_frequency_percentile": 0.3,  # 하위 30%
            "recent_activity_threshold": 0.2,    # 20% 이하
            "stability_score_threshold": 0.7     # 70% 이상
        }
    
    async def analyze_file_churn_metrics(self, repo_url: str, file_paths: List[str]) -> Dict[str, Any]:
        """파일별 변경 메트릭 분석"""
        
        churn_metrics = {}
        
        async with self.github_client as client:
            for file_path in file_paths:
                try:
                    # 파일별 커밋 이력 수집
                    commits = await client.get_file_commit_history(repo_url, file_path, limit=100)
                    
                    if not commits:
                        continue
                    
                    # 각종 메트릭 계산
                    metrics = {
                        "commit_frequency": len(commits),
                        "recent_activity": self._calculate_recent_activity(commits),
                        "author_diversity": self._calculate_author_diversity(commits),
                        "change_velocity": self._calculate_change_velocity(commits),
                        "stability_score": self._calculate_stability_score(commits),
                        "bug_fix_ratio": self._calculate_bug_fix_ratio(commits),
                        "refactor_ratio": self._calculate_refactor_ratio(commits),
                        "change_intensity": self._calculate_change_intensity(commits)
                    }
                    
                    churn_metrics[file_path] = metrics
                    
                except Exception as e:
                    print(f"Failed to analyze churn for {file_path}: {e}")
                    continue
        
        # 핫스팟 및 안정적인 파일 식별
        hotspot_files = self._identify_hotspots(churn_metrics)
        stable_files = self._identify_stable_files(churn_metrics)
        
        return {
            "file_churn_metrics": churn_metrics,
            "hotspot_files": hotspot_files,
            "stable_files": stable_files,
            "analysis_summary": self._generate_churn_summary(churn_metrics),
            "change_patterns": self.analyze_change_patterns_from_metrics(churn_metrics)
        }
    
    def _calculate_recent_activity(self, commits: List[Dict[str, Any]]) -> float:
        """최근 3개월 활동도 계산"""
        
        if not commits:
            return 0.0
        
        three_months_ago = datetime.now() - timedelta(days=90)
        recent_commits = 0
        
        for commit in commits:
            try:
                # ISO 형식의 날짜 파싱
                commit_date_str = commit.get("date", "")
                if commit_date_str.endswith('Z'):
                    commit_date_str = commit_date_str[:-1] + '+00:00'
                
                commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                if commit_date > three_months_ago:
                    recent_commits += 1
            except (ValueError, KeyError):
                # 날짜 파싱 실패시 최근 활동으로 간주하지 않음
                continue
        
        return recent_commits / len(commits)
    
    def _calculate_change_velocity(self, commits: List[Dict[str, Any]]) -> float:
        """변경 속도 계산 (시간 가중 평균)"""
        
        if not commits:
            return 0.0
        
        now = datetime.now()
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for commit in commits:
            try:
                commit_date_str = commit.get("date", "")
                if commit_date_str.endswith('Z'):
                    commit_date_str = commit_date_str[:-1] + '+00:00'
                
                commit_date = datetime.fromisoformat(commit_date_str)
                days_ago = (now - commit_date).days
                
                # 최근 커밋일수록 높은 가중치 (지수 감소)
                weight = 1.0 / (1.0 + days_ago / 30.0)  # 30일 기준
                
                # 변경 크기 (additions + deletions)
                additions = commit.get("additions", 0)
                deletions = commit.get("deletions", 0)
                change_size = additions + deletions
                
                weighted_sum += change_size * weight
                weight_sum += weight
                
            except (ValueError, KeyError):
                continue
        
        return weighted_sum / max(weight_sum, 1.0)
    
    def _calculate_author_diversity(self, commits: List[Dict[str, Any]]) -> int:
        """작성자 다양성 계산"""
        
        authors = set()
        for commit in commits:
            author = commit.get("author", "unknown")
            if author:
                authors.add(author)
        
        return len(authors)
    
    def _calculate_stability_score(self, commits: List[Dict[str, Any]]) -> float:
        """안정성 점수 계산"""
        
        if not commits:
            return 1.0  # 변경이 없으면 완전히 안정적
        
        # 기본 안정성 (커밋 빈도에 반비례)
        base_stability = 1.0 / (1.0 + len(commits) / 10.0)
        
        # 최근 활동도 페널티
        recent_activity = self._calculate_recent_activity(commits)
        activity_penalty = recent_activity * 0.3
        
        # 변경 크기 일관성 보너스
        change_sizes = []
        for commit in commits:
            additions = commit.get("additions", 0)
            deletions = commit.get("deletions", 0)
            change_sizes.append(additions + deletions)
        
        consistency_bonus = 0.0
        if len(change_sizes) > 1:
            # 변경 크기의 표준편차가 작을수록 일관성 높음
            std_dev = statistics.stdev(change_sizes)
            mean_change = statistics.mean(change_sizes)
            if mean_change > 0:
                cv = std_dev / mean_change  # 변동계수
                consistency_bonus = max(0, 0.2 - cv * 0.1)
        
        stability = base_stability - activity_penalty + consistency_bonus
        return max(0.0, min(1.0, stability))
    
    def _calculate_bug_fix_ratio(self, commits: List[Dict[str, Any]]) -> float:
        """버그 수정 커밋 비율 계산"""
        
        if not commits:
            return 0.0
        
        bug_fix_count = 0
        for commit in commits:
            message = commit.get("message", "").lower()
            if self._is_bug_fix_commit(message):
                bug_fix_count += 1
        
        return bug_fix_count / len(commits)
    
    def _calculate_refactor_ratio(self, commits: List[Dict[str, Any]]) -> float:
        """리팩토링 커밋 비율 계산"""
        
        if not commits:
            return 0.0
        
        refactor_count = 0
        for commit in commits:
            message = commit.get("message", "").lower()
            if self._is_refactor_commit(message):
                refactor_count += 1
        
        return refactor_count / len(commits)
    
    def _calculate_change_intensity(self, commits: List[Dict[str, Any]]) -> float:
        """변경 강도 계산 (총 변경 라인 수)"""
        
        total_changes = 0
        for commit in commits:
            additions = commit.get("additions", 0)
            deletions = commit.get("deletions", 0)
            total_changes += additions + deletions
        
        return total_changes
    
    def _is_bug_fix_commit(self, message: str) -> bool:
        """버그 수정 커밋 여부 판별"""
        
        for pattern in self.bug_fix_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _is_refactor_commit(self, message: str) -> bool:
        """리팩토링 커밋 여부 판별"""
        
        for pattern in self.refactor_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True
        return False
    
    def _detect_bug_fix_commits(self, commit_messages: List[str]) -> int:
        """버그 수정 커밋 개수 감지"""
        
        count = 0
        for message in commit_messages:
            if self._is_bug_fix_commit(message.lower()):
                count += 1
        return count
    
    def _detect_refactor_commits(self, commit_messages: List[str]) -> int:
        """리팩토링 커밋 개수 감지"""
        
        count = 0
        for message in commit_messages:
            if self._is_refactor_commit(message.lower()):
                count += 1
        return count
    
    def _identify_hotspots(self, churn_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """핫스팟 파일 식별 (통계적 방법)"""
        
        if not churn_metrics:
            return []
        
        hotspots = []
        
        # 각 메트릭별 임계값 계산
        commit_frequencies = [metrics["commit_frequency"] for metrics in churn_metrics.values()]
        change_intensities = [metrics["change_intensity"] for metrics in churn_metrics.values()]
        
        if not commit_frequencies:
            return []
        
        # 백분위수 기반 임계값
        commit_threshold = self._calculate_percentile(
            commit_frequencies, 
            self.hotspot_thresholds["commit_frequency_percentile"]
        )
        intensity_threshold = self._calculate_percentile(
            change_intensities,
            self.hotspot_thresholds["change_intensity_percentile"]
        )
        
        for file_path, metrics in churn_metrics.items():
            # 핫스팟 조건: 높은 커밋 빈도 + 높은 최근 활동도
            is_high_frequency = metrics["commit_frequency"] >= commit_threshold
            is_recent_active = metrics["recent_activity"] >= self.hotspot_thresholds["recent_activity_threshold"]
            is_high_intensity = metrics["change_intensity"] >= intensity_threshold
            
            if (is_high_frequency and is_recent_active) or is_high_intensity:
                hotspots.append(file_path)
        
        # 위험도 순으로 정렬
        hotspots.sort(key=lambda f: self.calculate_churn_risk_score(churn_metrics[f]), reverse=True)
        
        return hotspots
    
    def _identify_stable_files(self, churn_metrics: Dict[str, Dict[str, Any]]) -> List[str]:
        """안정적인 파일 식별"""
        
        if not churn_metrics:
            return []
        
        stable_files = []
        
        # 안정성 기준
        commit_frequencies = [metrics["commit_frequency"] for metrics in churn_metrics.values()]
        if not commit_frequencies:
            return []
        
        commit_threshold = self._calculate_percentile(
            commit_frequencies,
            self.stability_thresholds["commit_frequency_percentile"]
        )
        
        for file_path, metrics in churn_metrics.items():
            # 안정성 조건: 낮은 커밋 빈도 + 낮은 최근 활동도 + 높은 안정성 점수
            is_low_frequency = metrics["commit_frequency"] <= commit_threshold
            is_low_activity = metrics["recent_activity"] <= self.stability_thresholds["recent_activity_threshold"]
            is_stable = metrics["stability_score"] >= self.stability_thresholds["stability_score_threshold"]
            
            if is_low_frequency and is_low_activity and is_stable:
                stable_files.append(file_path)
        
        # 안정성 점수 순으로 정렬
        stable_files.sort(key=lambda f: churn_metrics[f]["stability_score"], reverse=True)
        
        return stable_files
    
    def _calculate_percentile(self, values: List[float], percentile: float) -> float:
        """백분위수 계산"""
        
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    def calculate_churn_risk_score(self, metrics: Dict[str, Any]) -> float:
        """변경 위험도 점수 계산"""
        
        # 가중치
        weights = {
            "commit_frequency": 0.3,
            "recent_activity": 0.25,
            "change_velocity": 0.2,
            "bug_fix_ratio": 0.15,
            "author_diversity": 0.1
        }
        
        # 정규화된 점수 계산
        normalized_scores = {}
        
        # 커밋 빈도 (로그 스케일 정규화)
        commit_freq = metrics.get("commit_frequency", 0)
        normalized_scores["commit_frequency"] = min(1.0, commit_freq / 20.0)
        
        # 최근 활동도 (이미 0-1 범위)
        normalized_scores["recent_activity"] = metrics.get("recent_activity", 0.0)
        
        # 변경 속도 (로그 스케일 정규화)
        velocity = metrics.get("change_velocity", 0.0)
        normalized_scores["change_velocity"] = min(1.0, velocity / 100.0)
        
        # 버그 수정 비율 (높을수록 위험)
        normalized_scores["bug_fix_ratio"] = metrics.get("bug_fix_ratio", 0.0)
        
        # 작성자 다양성 (많을수록 위험 - 일관성 부족)
        diversity = metrics.get("author_diversity", 1)
        normalized_scores["author_diversity"] = min(1.0, (diversity - 1) / 5.0)
        
        # 가중 평균으로 최종 위험도 계산
        risk_score = sum(
            normalized_scores[metric] * weights[metric]
            for metric in weights.keys()
        )
        
        return min(1.0, max(0.0, risk_score))
    
    def analyze_change_patterns(self, file_commit_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """변경 패턴 분석"""
        
        if not file_commit_data:
            return {}
        
        total_files = len(file_commit_data)
        total_commits = sum(len(commits) for commits in file_commit_data.values())
        
        # 가장 활발한 파일
        most_active_file = None
        max_commits = 0
        for file_path, commits in file_commit_data.items():
            if len(commits) > max_commits:
                max_commits = len(commits)
                most_active_file = file_path
        
        # 변경 분포
        commit_counts = [len(commits) for commits in file_commit_data.values()]
        change_distribution = {
            "mean": statistics.mean(commit_counts) if commit_counts else 0,
            "median": statistics.median(commit_counts) if commit_counts else 0,
            "std_dev": statistics.stdev(commit_counts) if len(commit_counts) > 1 else 0
        }
        
        return {
            "total_files": total_files,
            "total_commits": total_commits,
            "average_commits_per_file": round(total_commits / max(total_files, 1), 2),
            "most_active_file": {
                "path": most_active_file,
                "commit_count": max_commits
            },
            "change_distribution": change_distribution
        }
    
    def analyze_change_patterns_from_metrics(self, churn_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """메트릭으로부터 변경 패턴 분석"""
        
        if not churn_metrics:
            return {}
        
        files = list(churn_metrics.keys())
        commit_frequencies = [metrics["commit_frequency"] for metrics in churn_metrics.values()]
        
        return {
            "total_files_analyzed": len(files),
            "average_commit_frequency": round(statistics.mean(commit_frequencies), 2) if commit_frequencies else 0,
            "max_commit_frequency": max(commit_frequencies) if commit_frequencies else 0,
            "min_commit_frequency": min(commit_frequencies) if commit_frequencies else 0,
            "high_activity_files": len([f for f, m in churn_metrics.items() if m["recent_activity"] > 0.5])
        }
    
    def calculate_integrated_risk_scores(
        self, 
        dependency_centrality: Dict[str, float], 
        churn_metrics: Dict[str, Dict[str, Any]]
    ) -> Dict[str, float]:
        """의존성 중심성과 변경 이력을 통합한 위험도 점수"""
        
        integrated_scores = {}
        
        for file_path in set(dependency_centrality.keys()) | set(churn_metrics.keys()):
            centrality = dependency_centrality.get(file_path, 0.0)
            metrics = churn_metrics.get(file_path, {})
            
            if metrics:
                churn_risk = self.calculate_churn_risk_score(metrics)
            else:
                churn_risk = 0.0
            
            # 통합 점수: 의존성 중심성과 변경 위험도의 가중 평균
            # 높은 중심성 + 높은 변경 빈도 = 매우 위험
            integrated_score = (centrality * 0.4) + (churn_risk * 0.6)
            integrated_scores[file_path] = integrated_score
        
        return integrated_scores
    
    def get_churn_summary(self, file_commit_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """변경 이력 요약 정보"""
        
        if not file_commit_data:
            return {
                "total_files_analyzed": 0,
                "total_commits": 0,
                "most_active_file": None,
                "average_commits_per_file": 0.0,
                "hotspot_count": 0,
                "stable_file_count": 0
            }
        
        total_files = len(file_commit_data)
        total_commits = sum(len(commits) for commits in file_commit_data.values())
        
        # 가장 활발한 파일
        most_active_file = None
        max_commits = 0
        for file_path, commits in file_commit_data.items():
            if len(commits) > max_commits:
                max_commits = len(commits)
                most_active_file = file_path
        
        # 임시 메트릭 계산 (간단한 버전)
        hotspot_count = 0
        stable_count = 0
        
        for file_path, commits in file_commit_data.items():
            commit_count = len(commits)
            if commit_count > 5:  # 임의 임계값
                hotspot_count += 1
            elif commit_count <= 2:
                stable_count += 1
        
        return {
            "total_files_analyzed": total_files,
            "total_commits": total_commits,
            "most_active_file": {
                "path": most_active_file,
                "commit_count": max_commits
            },
            "average_commits_per_file": round(total_commits / max(total_files, 1), 2),
            "hotspot_count": hotspot_count,
            "stable_file_count": stable_count
        }
    
    def _generate_churn_summary(self, churn_metrics: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Churn 메트릭 요약 생성"""
        
        if not churn_metrics:
            return {}
        
        files = list(churn_metrics.keys())
        commit_frequencies = [metrics["commit_frequency"] for metrics in churn_metrics.values()]
        recent_activities = [metrics["recent_activity"] for metrics in churn_metrics.values()]
        stability_scores = [metrics["stability_score"] for metrics in churn_metrics.values()]
        
        return {
            "total_files": len(files),
            "average_commit_frequency": round(statistics.mean(commit_frequencies), 2),
            "average_recent_activity": round(statistics.mean(recent_activities), 3),
            "average_stability": round(statistics.mean(stability_scores), 3),
            "most_changed_file": max(churn_metrics.items(), key=lambda x: x[1]["commit_frequency"])[0],
            "most_stable_file": max(churn_metrics.items(), key=lambda x: x[1]["stability_score"])[0]
        }