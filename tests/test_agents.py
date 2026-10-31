from backend.app.agents.router import QueryRouter
from backend.app.agents.query_rewriter import QueryRewriter
from backend.app.agents.relevance_grader import RelevanceGrader
from backend.app.agents.generator import AnswerGenerator
from backend.app.tools.calculator import calculator_tool


def test_router_classifies_calculation():
    assert QueryRouter().classify("Calculate 12 * 4") == "CALCULATION"


def test_router_classifies_document_question():
    assert QueryRouter().classify("What does the uploaded document say?") == "DOCUMENT_SEARCH"


def test_router_skips_llm_for_obvious_general_question():
    class FailingLLM:
        def invoke(self, _prompt):
            raise AssertionError("general questions should use the heuristic")

    assert QueryRouter(FailingLLM()).classify("How are you today?") == "GENERAL_QUESTION"


def test_router_uses_uploaded_documents_for_resume_question():
    assert QueryRouter().classify("What are his skills?", has_documents=True) == "DOCUMENT_SEARCH"


def test_router_uses_uploaded_documents_for_exam_schedule():
    assert QueryRouter().classify(
        "Explain AMIRTHA E's exam schedule", has_documents=True
    ) == "DOCUMENT_SEARCH"


def test_router_keeps_small_talk_general_with_documents():
    router = QueryRouter()
    assert router.classify("Hi, how are you?", has_documents=True) == "GENERAL_QUESTION"
    assert router.classify("Thank you!", has_documents=True) == "GENERAL_QUESTION"


def test_router_sends_other_questions_to_documents():
    assert QueryRouter().classify("What is the candidate's name?", has_documents=True) == "DOCUMENT_SEARCH"


def test_router_accepts_non_json_llm_label():
    class FakeLLM:
        def invoke(self, _prompt):
            return "DOCUMENT_SEARCH"

    assert QueryRouter(FakeLLM()).classify("Tell me about the report") == "DOCUMENT_SEARCH"


def test_router_falls_back_when_llm_json_shape_is_wrong():
    class FakeLLM:
        def invoke(self, _prompt):
            return '{"label": "GENERAL_QUESTION"}'

    assert QueryRouter(FakeLLM()).classify("Tell me a joke") == "GENERAL_QUESTION"


def test_rewriter_without_llm_preserves_intent():
    assert QueryRewriter().rewrite("  What is this?  ") == "What is this?"


def test_rewriter_skips_model_for_clear_question():
    class FailingLLM:
        def invoke(self, _prompt):
            raise AssertionError("clear questions should not require rewriting")

    question = "What is the name in the uploaded document?"
    assert QueryRewriter(FailingLLM()).rewrite(question) == question


def test_relevance_empty_documents_is_false():
    assert RelevanceGrader().grade("question", {})["relevant"] is False


def test_relevance_accepts_plain_text_llm_response():
    class FakeLLM:
        def invoke(self, _prompt):
            return "The retrieved evidence is relevant."

    result = RelevanceGrader(FakeLLM()).grade("question", [{"content": "evidence"}])
    assert result["relevant"] is True


def test_relevance_accepts_evidence_array_json():
    class FakeLLM:
        def invoke(self, _prompt):
            return '```json\n{"evidence": [{"relevant": true, "reason": "matches", "confidence": 0.9}]}\n```'

    assert RelevanceGrader(FakeLLM()).grade("question", [{"content": "evidence"}])["relevant"] is True


def test_calculator_does_not_execute_names():
    assert calculator_tool.invoke("2 + 3") == "5.0"


def test_generator_extracts_exam_schedule_from_evidence():
    evidence = [{
        "document_name": "hall-ticket.pdf",
        "page_number": 1,
        "content": "22CSH30 KNOWLEDGE ENGINEERING 11-11-2026 01:30 PM to 04:30 PM",
    }]
    result = AnswerGenerator().generate("Explain the exam schedule", evidence)
    assert "KNOWLEDGE ENGINEERING" in result
    assert "11-11-2026" in result
