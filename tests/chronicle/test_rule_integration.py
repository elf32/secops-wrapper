#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Integration tests for rule deployment endpoints in Chronicle API.

These tests require valid credentials and API access.
"""
import pytest
from secops import SecOpsClient
from ..config import CHRONICLE_CONFIG, SERVICE_ACCOUNT_JSON


def _first_rule_id(chronicle) -> str:
    """Helper to fetch a rule id from list_rules response."""
    rules = chronicle.list_rules(view="BASIC")
    items = rules.get("rules", [])
    if not items:
        return ""
    return items[0]["name"].split("/")[-1]


@pytest.mark.integration
def test_rule_get_deployment_integration():
    """Get deployment for the first available rule."""
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    rule_id = _first_rule_id(chronicle)
    if not rule_id:
        pytest.skip("No rules available to fetch deployment for")

    result = chronicle.get_rule_deployment(rule_id)
    assert isinstance(result, dict)
    assert "name" in result


@pytest.mark.integration
def test_rule_list_deployments_integration():
    """List rule deployments"""
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    # Small page to force pagination when possible
    first = chronicle.list_rule_deployments(page_size=1)
    assert isinstance(first, dict)
    deployments = first.get("ruleDeployments", [])

    # If we have at least one item, the schema should be dicts
    if deployments:
        assert isinstance(deployments[0], dict)

    # If there's a next page token, fetch the next page and ensure pagination works
    token = first.get("nextPageToken")
    if token:
        second = chronicle.list_rule_deployments(page_size=1, page_token=token)
        assert isinstance(second, dict)
        deployments2 = second.get("ruleDeployments", [])
        if deployments and deployments2:
            # First items from each page should differ
            assert deployments[0].get("name") != deployments2[0].get("name")


@pytest.mark.integration
def test_rule_update_deployment_alerting_integration():
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    rule_id = _first_rule_id(chronicle)
    if not rule_id:
        pytest.skip("No rules available to update deployment for")

    before = chronicle.get_rule_deployment(rule_id)
    prev_alerting = before.get("alerting", False)

    try:
        target = not bool(prev_alerting)
        res = chronicle.update_rule_deployment(rule_id=rule_id, alerting=target)
        assert isinstance(res, dict)
        assert res.get("alerting", False) == target
    finally:
        try:
            chronicle.update_rule_deployment(
                rule_id=rule_id, alerting=prev_alerting
            )
        except Exception:
            pass


@pytest.mark.integration
def test_rule_update_deployment_enabled_integration():
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    rule_id = _first_rule_id(chronicle)
    if not rule_id:
        pytest.skip("No rules available to update deployment for")

    before = chronicle.get_rule_deployment(rule_id)
    prev_enabled = before.get("enabled", False)
    prev_archived = before.get("archived", False)
    if prev_archived:
        pytest.skip("Rule is archived; cannot toggle enabled")

    try:
        res = chronicle.update_rule_deployment(
            rule_id=rule_id, enabled=not bool(prev_enabled)
        )
        assert isinstance(res, dict)
        assert res.get("enabled", False) is not bool(prev_enabled)
    finally:
        try:
            chronicle.update_rule_deployment(
                rule_id=rule_id, enabled=prev_enabled
            )
        except Exception:
            pass


@pytest.mark.integration
def test_rule_update_deployment_archived_integration():
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    rule_id = _first_rule_id(chronicle)
    if not rule_id:
        pytest.skip("No rules available to update deployment for")

    before = chronicle.get_rule_deployment(rule_id)
    prev_archived = before.get("archived", False)

    try:
        # To archive, enabled must be false; set both in one call
        res = chronicle.update_rule_deployment(
            rule_id=rule_id,
            archived=not prev_archived,
        )
        assert isinstance(res, dict)
        assert res.get("archived", False) is not prev_archived
    finally:
        try:
            # Restore previous archived/enabled state
            chronicle.update_rule_deployment(
                rule_id=rule_id, archived=prev_archived
            )
        except Exception:
            pass


@pytest.mark.integration
def test_rule_update_deployment_run_frequency_integration():
    client = SecOpsClient(service_account_info=SERVICE_ACCOUNT_JSON)
    chronicle = client.chronicle(**CHRONICLE_CONFIG)

    rule_id = _first_rule_id(chronicle)
    if not rule_id:
        pytest.skip("No rules available to update deployment for")

    before = chronicle.get_rule_deployment(rule_id)
    prev_run = before.get("runFrequency")

    target = "LIVE" if prev_run != "LIVE" else "HOURLY"

    try:
        res = chronicle.update_rule_deployment(
            rule_id=rule_id, run_frequency=target
        )
        assert isinstance(res, dict)
        assert res.get("runFrequency") is not None
    finally:
        try:
            chronicle.update_rule_deployment(
                rule_id=rule_id, run_frequency=prev_run
            )
        except Exception:
            pass