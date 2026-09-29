import unittest

from email_policy import is_email_allowed


class EmailPolicyTests(unittest.TestCase):
    def test_allows_institutional_domain(self):
        self.assertTrue(is_email_allowed("person@udf.edu.br"))

    def test_allows_exact_configured_developer_address(self):
        self.assertTrue(
            is_email_allowed(
                " Reviewer@cs.udf.edu.br ",
                "reviewer@cs.udf.edu.br",
            )
        )

    def test_does_not_allow_an_unlisted_subdomain_address(self):
        self.assertFalse(is_email_allowed("person@cs.udf.edu.br"))

    def test_does_not_allow_a_domain_suffix_spoof(self):
        self.assertFalse(is_email_allowed("person@udf.edu.br.attacker.example"))

    def test_rejects_missing_or_malformed_values(self):
        for email in (None, "", "not-an-email", "@udf.edu.br"):
            with self.subTest(email=email):
                self.assertFalse(is_email_allowed(email))


if __name__ == "__main__":
    unittest.main()
