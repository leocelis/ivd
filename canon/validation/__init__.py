# canon/validation/__init__.py
"""
Canon validation scripts — run locally to verify Canon integration end-to-end.

  validate_engine.py  — Option A: deterministic engine run, no API key
  validate_mcp.py     — Option B: real MCP JSON-RPC over stdio, no API key
  validate_rules.py   — Option C: LLM effectiveness test, needs API key

Run each from the ivd/ root:
    python -m canon.validation.validate_engine
    python -m canon.validation.validate_mcp
    python -m canon.validation.validate_rules
"""
