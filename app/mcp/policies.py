from __future__ import annotations

from app.mcp.schemas import PolicyBundle, PolicyCategory, PolicyRule


DEFAULT_POLICY = PolicyBundle(
    policy_id="healthcare-claims-v1",
    name="Healthcare Claims Processing Policy",
    category=PolicyCategory.validation,
    allowed_procedures=[
        "99213",
        "99214",
        "45378",
        "A0428",
        "81002",
        "36415",
        "93000",
    ],
    max_line_item_amount=12500.0,
    exceptions={
        "providers": ["P-99999"],
    },
    rules=[
        PolicyRule(
            rule_id="rule-001",
            description="Reject procedures not in the allowed procedure list.",
            severity="high",
            conditions={"procedure_not_allowed": True},
            actions=["reject"],
        ),
        PolicyRule(
            rule_id="rule-002",
            description="Flag claims with line item values greater than policy maximum.",
            severity="medium",
            conditions={"amount_exceeds_max": True},
            actions=["review"],
        ),
    ],
)
