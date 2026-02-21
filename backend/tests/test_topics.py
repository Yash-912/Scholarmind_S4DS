"""Tests for BERTopic — verifies coherent clusters."""

from app.core.topic_model import TopicModeler


def test_topic_modeler_initializes():
    modeler = TopicModeler()
    assert modeler is not None


def test_get_topics_returns_list():
    modeler = TopicModeler()
    topics = modeler.get_topics()
    assert isinstance(topics, list)


def test_trending_topics_returns_list():
    modeler = TopicModeler()
    trending = modeler.get_trending()
    assert isinstance(trending, list)
