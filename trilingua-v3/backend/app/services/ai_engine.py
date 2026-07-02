"""AI provider abstraction — scaffolding for OpenAI, Claude, DeepSeek calls.

To be implemented: translate_text, coach_reply, grammar_correct, etc.
Each function will follow the V2 prompt architecture (language_rules,
strict_language_guard, quality_guard) adapted for async FastAPI.
"""
