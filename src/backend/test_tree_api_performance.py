#!/usr/bin/env python3
"""
Tree API 성능 테스트 스크립트
기존 Contents API vs 새로운 Tree API 성능 비교
"""
import asyncio
import time
import json
from app.api.github import RepositoryAnalyzer

async def test_tree_api_performance():
    """Tree API 성능 테스트"""
    
    # 테스트할 대형 저장소 (Node.js 저장소는 매우 크므로)
    test_repos = [
        ("nodejs", "node"),        # Node.js (매우 큰 저장소)
        ("microsoft", "vscode"),   # VS Code (큰 저장소)
        ("facebook", "react")      # React (중간 크기)
    ]
    
    # Repository Analyzer 초기화
    analyzer = RepositoryAnalyzer()
    
    print("=== Tree API 성능 테스트 시작 ===\n")
    
    for owner, repo in test_repos:
        print(f"🔍 테스트 저장소: {owner}/{repo}")
        
        try:
            # Tree API 방식으로 파일 목록 조회
            start_time = time.time()
            
            print(f"  Tree API로 파일 목록 조회 중...")
            files = await analyzer.get_all_files(owner, repo)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"  ✅ Tree API 완료:")
            print(f"     - 소요 시간: {duration:.2f}초")
            print(f"     - 총 파일 수: {len(files)}")
            print(f"     - 평균 처리 속도: {len(files)/duration:.1f} 파일/초")
            
            # 파일 타입별 분석
            file_types = {}
            for file_node in files:
                if hasattr(file_node, 'path') and file_node.path:
                    ext = file_node.path.split('.')[-1] if '.' in file_node.path else 'no_ext'
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # 상위 5개 파일 타입 출력
            top_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"     - 주요 파일 타입: {', '.join([f'{ext}({count})' for ext, count in top_types])}")
            
        except Exception as e:
            print(f"  ❌ 테스트 실패: {e}")
        
        print()
        
        # API Rate Limit 방지를 위한 대기
        if owner != test_repos[-1][0]:  # 마지막이 아니면 대기
            print("  ⏳ Rate Limit 방지를 위해 5초 대기...")
            await asyncio.sleep(5)
    
    print("=== Tree API 성능 테스트 완료 ===")

async def test_specific_node_repo():
    """Node.js 저장소로 집중 테스트 (이전에 56초 걸렸던 케이스)"""
    
    print("=== Node.js 저장소 집중 테스트 ===\n")
    
    analyzer = RepositoryAnalyzer()
    
    try:
        print("🔍 Node.js 저장소 (nodejs/node) 분석 시작...")
        print("   이전 성능: Contents API로 56초+ 소요")
        print("   목표 성능: Tree API로 5-8초 달성\n")
        
        start_time = time.time()
        
        # Tree API로 파일 목록 조회
        files = await analyzer.get_all_files("nodejs", "node")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Tree API 결과:")
        print(f"   - 총 소요 시간: {duration:.2f}초")
        print(f"   - 성능 개선 비율: {56/duration:.1f}x 더 빠름")
        print(f"   - 총 파일 수: {len(files):,}개")
        print(f"   - 초당 처리 파일: {len(files)/duration:.0f}개/초")
        
        # 중요한 파일들 확인
        important_files = [f for f in files if hasattr(f, 'path') and any(pattern in f.path for pattern in ['package.json', 'src/', 'lib/', 'README'])]
        print(f"   - 주요 파일 발견: {len(important_files)}개")
        
        # 파일 크기별 분석  
        large_files = [f for f in files if hasattr(f, 'size') and f.size and f.size > 100000]  # 100KB 이상
        print(f"   - 대용량 파일 (100KB+): {len(large_files)}개")
        
        # 성능 평가
        if duration < 10:
            print(f"\n🎉 성능 목표 달성! Tree API가 {duration:.2f}초 만에 완료")
        else:
            print(f"\n⚠️  목표 미달성. 추가 최적화 필요: {duration:.2f}초")
            
    except Exception as e:
        print(f"❌ Node.js 저장소 테스트 실패: {e}")
    
    print("\n=== Node.js 저장소 테스트 완료 ===")

async def main():
    """메인 테스트 실행"""
    
    print("Tree API 성능 측정 도구")
    print("=" * 50)
    
    # 1. 다양한 저장소로 일반 테스트
    await test_tree_api_performance()
    
    print("\n" + "=" * 50)
    
    # 2. Node.js 저장소 집중 테스트
    await test_specific_node_repo()

if __name__ == "__main__":
    asyncio.run(main())