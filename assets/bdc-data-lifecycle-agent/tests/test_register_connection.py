"""Test register_connection — refuses without confirmation; calls Connections MCP when confirmed."""
import logging
from tests._helpers import parse_result
from tools import _register_connection, _confirmed_actions


def test_register_refuses_without_confirmation():
    _confirmed_actions.discard("register_connection:UnconfirmedSys")
    result = parse_result(_register_connection(
        system_name="UnconfirmedSys",
        protocol="REST",
        connection_params="{}",
        target_space="space_01",
    ))
    assert "error" in result


def test_register_succeeds_when_confirmed():
    result = parse_result(_register_connection(
        system_name="ConfirmedSys",
        protocol="REST",
        connection_params='{"base_url": "https://api.example.com"}',
        target_space="space_01",
        confirmed=True,
    ))
    assert result["tool"] == "register_connection"
    assert "connection_registration_initiated" in result["status"]


def test_register_emits_m3_achieved_log(caplog):
    with caplog.at_level(logging.INFO):
        _register_connection(
            system_name="LoggedSys",
            protocol="JDBC",
            connection_params='{}',
            target_space="space_01",
            confirmed=True,
        )
    assert any("M3.achieved" in r.message for r in caplog.records)


def test_register_warns_m3_missed_when_refused(caplog):
    _confirmed_actions.discard("register_connection:MissSys")
    with caplog.at_level(logging.WARNING):
        _register_connection(
            system_name="MissSys",
            protocol="REST",
            connection_params="{}",
            target_space="space_01",
        )
    assert any("M3.missed" in r.message for r in caplog.records)
