import os
import sys
from pathlib import Path

# Add project root to sys.path so 'backend' is importable
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT_DIR / ".env")
except ImportError:
    pass

from backend.app.llm.providers import get_llm_provider, NoneProvider, GeminiProvider

SAMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "metric": {"type": "string"},
                    "claim_type": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string"},
                    "period": {"type": "string"},
                    "entity": {"type": "string"}
                },
                "required": ["quote", "metric", "claim_type", "value", "unit", "period", "entity"]
            }
        }
    },
    "required": ["claims"]
}

def main():
    print("=== Task 0.5: LLM Provider & Fallback Test ===")
    
    # 1. Test Fallback (NoneProvider)
    none_provider = NoneProvider()
    res = none_provider.complete_json("system", "user text", SAMPLE_SCHEMA)
    assert res is None, f"Expected None from NoneProvider, got: {res}"
    print("[PASS] Fallback test (NoneProvider): PASSED (returned None cleanly)")

    # 2. Test configured provider via environment
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        print("[INFO] GEMINI_API_KEY not found in environment.")
        print("       To test live Gemini calls, set GEMINI_API_KEY=<key> in .env or your shell.")
        print("       Active fallback provider:", type(get_llm_provider()).__name__)
        print("[PASS] All offline contract checks PASSED.")
        return

    provider = get_llm_provider()
    print(f"Calling live provider: {type(provider).__name__} (model: {getattr(provider, 'model', 'N/A')})...")
    
    test_user_prompt = "In FY2025, Veridian Foods Ltd reported revenue grew by 25 percent."
    test_system_prompt = "You are a financial claim extraction assistant. Extract factual claims strictly conforming to the JSON schema."
    
    result = provider.complete_json(test_system_prompt, test_user_prompt, SAMPLE_SCHEMA)
    if result is not None and "claims" in result:
        print("[PASS] Live Gemini JSON test: PASSED")
        print("Extracted claims payload:")
        import json
        print(json.dumps(result, indent=2))
    else:
        print("[FAIL] Provider returned:", result)
        sys.exit(1)

if __name__ == "__main__":
    main()
