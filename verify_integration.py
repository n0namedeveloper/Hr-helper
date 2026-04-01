#!/usr/bin/env python3
"""Verification script for Perplexity API integration."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def check_imports():
    """Verify all agents and modules import correctly."""
    checks = []
    
    # Check config
    try:
        from hr_breaker.config import get_settings
        settings = get_settings()
        assert settings.perplexity_api_key, "PERPLEXITY_API_KEY not set"
        checks.append(("✓ Config loads", True))
        checks.append((f"  - API key present: {bool(settings.perplexity_api_key)}", True))
        checks.append((f"  - Pro model: {settings.perplexity_pro_model}", True))
        checks.append((f"  - Flash model: {settings.perplexity_flash_model}", True))
    except Exception as e:
        checks.append(("✗ Config loading failed", False))
        checks.append((f"  - Error: {e}", False))
        return checks
    
    # Check all agents
    agents_to_check = [
        ("job_parser", "from hr_breaker.agents.job_parser import get_job_parser_agent"),
        ("optimizer", "from hr_breaker.agents.optimizer import get_optimizer_agent"),
        ("hallucination_detector", "from hr_breaker.agents.hallucination_detector import get_hallucination_agent"),
        ("ai_generated_detector", "from hr_breaker.agents.ai_generated_detector import get_ai_generated_agent"),
        ("combined_reviewer", "from hr_breaker.agents.combined_reviewer import get_combined_reviewer_agent"),
        ("name_extractor", "from hr_breaker.agents.name_extractor import extract_name"),
    ]
    
    for agent_name, import_stmt in agents_to_check:
        try:
            exec(import_stmt)
            checks.append((f"✓ Agent '{agent_name}' imports", True))
        except Exception as e:
            checks.append((f"✗ Agent '{agent_name}' import failed", False))
            checks.append((f"  - Error: {e}", False))
    
    # Check perplexity_client
    try:
        from hr_breaker.agents.perplexity_client import create_perplexity_agent
        checks.append(("✓ Perplexity client helper imports", True))
    except Exception as e:
        checks.append(("✗ Perplexity client helper import failed", False))
        checks.append((f"  - Error: {e}", False))
    
    # Check orchestration
    try:
        from hr_breaker.orchestration import optimize_for_job
        checks.append(("✓ Orchestration module imports", True))
    except Exception as e:
        checks.append(("✗ Orchestration import failed", False))
        checks.append((f"  - Error: {e}", False))
    
    return checks


def main():
    """Run all checks."""
    print("\n" + "="*60)
    print("Perplexity API Integration - Verification")
    print("="*60 + "\n")
    
    checks = check_imports()
    
    passed = sum(1 for _, result in checks if result)
    total = len(checks)
    
    for message, result in checks:
        prefix = "" if result else ""
        print(f"{message}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} checks passed")
    print("="*60 + "\n")
    
    if passed == total:
        print("✓ All systems ready for use!")
        print("\nReady to run:")
        print("  uv run streamlit run src/hr_breaker/main.py")
        print("  uv run hr-breaker optimize <resume> <job>")
        return 0
    else:
        print("✗ Some checks failed. Review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
