from app.taxonomy import appears_english, classify_repo


def test_classifies_ai_agent_repo_from_topics_and_text():
    sectors = classify_repo(["ai-agent", "python"], "Autonomous agent workflow tools", "", "Python")
    assert "ai-agents" in sectors


def test_classifies_data_analytics_repo():
    sectors = classify_repo([], "A dashboard for warehouse analytics and metrics", "", "Python")
    assert "data-analytics" in sectors


def test_english_filter_includes_short_or_english_text():
    assert appears_english("CLI for building local developer dashboards with Python")
    assert appears_english("Tiny")


def test_english_filter_rejects_clear_non_english_text():
    assert not appears_english("这是一个用于构建数据分析和可视化工具的开源项目，支持多种工作流程。")
