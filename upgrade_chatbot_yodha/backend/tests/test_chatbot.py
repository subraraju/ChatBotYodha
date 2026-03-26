"""
Tests for the chatbot state machine.
"""

from app.chatbot import CustomerServiceBot, ChatSession, State


def test_start_session():
    bot = CustomerServiceBot()
    session = bot.start_session()
    assert session.state == State.COLLECTING_INFO
    assert len(session.messages) == 1
    assert session.messages[0]["role"] == "assistant"


def test_is_closing():
    assert CustomerServiceBot._is_closing("bye")
    assert CustomerServiceBot._is_closing("goodbye!")
    assert CustomerServiceBot._is_closing("exit")
    assert not CustomerServiceBot._is_closing("hello")


def test_is_marketing_request():
    assert CustomerServiceBot._is_marketing_request("schedule a meeting")
    assert CustomerServiceBot._is_marketing_request("I want to book a call")
    assert not CustomerServiceBot._is_marketing_request("tell me about the product")


def test_is_product_switch():
    assert CustomerServiceBot._is_product_switch("switch product")
    assert CustomerServiceBot._is_product_switch("go back")
    assert not CustomerServiceBot._is_product_switch("tell me more")
