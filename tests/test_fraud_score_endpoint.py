import unittest

from fastapi.testclient import TestClient

from app.mcp.server import app


class FraudScoreEndpointTests(unittest.TestCase):
    def test_accepts_nullable_item_fields(self) -> None:
        client = TestClient(app)
        response = client.post(
            "/fraud-score",
            json={
                "claim_id": "CLAIM-1001",
                "items": [
                    {
                        "procedure_code": None,
                        "amount": None,
                        "provider": None,
                        "diagnosis": None,
                    }
                ],
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["claim_id"], "CLAIM-1001")
        self.assertIn("fraud_score", body)


if __name__ == "__main__":
    unittest.main()
