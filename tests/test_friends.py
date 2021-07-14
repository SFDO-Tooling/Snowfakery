from io import StringIO

from snowfakery.data_generator import generate


class TestFriends:
    def test_multiple_friends(self, generated_rows):
        yaml = """
        - object: Account
        - object: Account
          friends:
            - object: Contact
              fields:
                AccountId:
                    reference: Account
            - object: Contact
              fields:
                AccountId:
                    reference: Account
        """
        generate(StringIO(yaml), {})
        assert generated_rows.table_values("Contact", 0, "AccountId") == "Account(2)"
        assert generated_rows.table_values("Contact", 1, "AccountId") == "Account(2)"
