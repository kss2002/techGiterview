
import sys
import os
import asyncio
from unittest.mock import MagicMock

# Add src/backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'src', 'backend'))
# Also try adding the parent directory just in case
sys.path.append(os.path.join(os.getcwd(), '..'))

# Mocking heavy dependencies to avoid ImportError in lightweight test
sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.messages'] = MagicMock()
sys.modules['langchain_core.prompts'] = MagicMock()
sys.modules['langchain_core.output_parsers'] = MagicMock()
sys.modules['langgraph'] = MagicMock()
sys.modules['langgraph.graph'] = MagicMock()

from app.agents.repository_analyzer import RepositoryAnalyzer

def test_phase_1_metadata_scoring():
    print("\n[TEST] Phase 1: Metadata Scoring Verification")
    
    # Mock Analyzer
    analyzer = RepositoryAnalyzer()
    analyzer.smart_file_analyzer = MagicMock()
    
    # Configure SmartFileImportanceAnalyzer mocks
    analyzer.smart_file_analyzer.is_excluded_file.return_value = False
    analyzer.smart_file_analyzer.calculate_structural_importance.return_value = 0.5
    
    # Mock File Tree
    file_tree = [
        {"path": "tests/test_gemini.py", "type": "file", "size": 5000},
        {"path": "src/backend/app/api/interview.py", "type": "file", "size": 2000},
        {"path": "services/feedback.py", "type": "file", "size": 3000},
        {"path": "README.md", "type": "file", "size": 1000},
    ]
    
    # Run Scoring
    scores = analyzer._build_metadata_for_scoring(file_tree)
    
    # Assertions
    print(f"Scores: {scores}")
    
    # Check Test Penalty
    test_score = scores.get("tests/test_gemini.py")
    if test_score == 0.01:
        print("✅ PASS: Test file score is strictly 0.01")
    else:
        print(f"❌ FAIL: Test file score is {test_score}, expected 0.01")

    # Check Vendor Penalty
    vendor_score = scores.get("deps/v8/tools/gen.py")
    if vendor_score == 0.01:
        print("✅ PASS: Vendor/Deps file score is strictly 0.01")
    else:
        print(f"❌ FAIL: Vendor file score is {vendor_score}, expected 0.01")
        
    # Check Logic Boost
    logic_score = scores.get("src/backend/app/api/interview.py")
    lib_score = scores.get("lib/http.js")
    
    # Base calculation: (size_score * 0.3) + (struct_score * 0.7) + 0.5 (Boost)
    # size ~ 0.2, struct = 0.5 -> (0.06 + 0.35) = 0.41 + 0.5 = 0.91
    if logic_score > 0.8:
        print(f"✅ PASS: Logic file verification score is high ({logic_score:.4f})")
    else:
        print(f"❌ FAIL: Logic file score {logic_score} is too low")

    if lib_score and lib_score > 0.8:
        print(f"✅ PASS: Lib file (nodejs core) score is high ({lib_score:.4f})")
    else:
        print(f"❌ FAIL: Lib file score {lib_score} is too low")

def test_phase_5_hybrid_selection_logic():
    print("\n[TEST] Phase 5: Hybrid Selection Logic Verification")
    
    # Simulate the logic block inside _select_important_files
    # We can't easily call the method because it requires async downloads, but we can verify the logic snippet.
    
    weighted_scores = {
        "tests/test_gemini.py": 0.85,    # High PageRank (simulated)
        "src/api/interview.py": 0.40,    # Lower PageRank
        "deps/v8/tools/gen.py": 0.70,    # Vendor file with high PageRank
        "README.md": 0.60
    }
    
    print(f"Original Scores: {weighted_scores}")
    
    paths = list(weighted_scores.keys())
    
    for path in paths:
        # --- LOGIC UNDER TEST (COPIED FROM RepositoryAnalyzer) ---
            is_test = 'test' in path.lower() or 'conftest' in path or 'spec' in path
            is_vendor = any(x in path.lower() for x in ['deps/', 'vendor/', 'node_modules/'])

            if not is_test and not is_vendor and any(x in path for x in ['api/', 'services/', 'core/', 'models/', 'lib/', 'src/', 'utils/', 'backend/app/', 'src/app/']):
                weighted_scores[path] *= 3.0 # Massive Boost (was 1.5)
            
            # Penalty: Tests & Vendor
            if is_test or is_vendor:
                weighted_scores[path] = 0.0  # NUCLEAR OPTION: Tests/Vendor get ZERO score.
        # ---------------------------------------------------------
    
    print(f"Final Scores:    {weighted_scores}")
    
    # Assertions
    if weighted_scores["tests/test_gemini.py"] == 0.0:
        print("✅ PASS: Test file score strictly forced to 0.0")
    else:
        print(f"❌ FAIL: Test file score is {weighted_scores['tests/test_gemini.py']}, expected 0.0")

    if weighted_scores["deps/v8/tools/gen.py"] == 0.0:
        print("✅ PASS: Vendor file score strictly forced to 0.0")
    else:
        print(f"❌ FAIL: Vendor file score is {weighted_scores['deps/v8/tools/gen.py']}, expected 0.0")

    if weighted_scores["src/api/interview.py"] > 1.0:
        print(f"✅ PASS: Logic file boosted correctly ({weighted_scores['src/api/interview.py']})")
    else:
        print("❌ FAIL: Logic file not boosted enough")

if __name__ == "__main__":
    test_phase_1_metadata_scoring()
    test_phase_5_hybrid_selection_logic()
