from io import StringIO
from unittest import mock
from datetime import date, datetime, timezone

import pytest
from dateutil import parser as dateparser
from snowfakery.data_generator import generate
from snowfakery import data_gen_exceptions as exc

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_row"


def row_values(write_row_mock, index, value):
    return write_row_mock.mock_calls[index][1][1][value]


class TestFaker:
    @mock.patch(write_row_path)
    def test_fake_block_simple(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            first_name:
                fake:
                    first_name
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "first_name")

    @mock.patch(write_row_path)
    def test_fake_block_simple_oneline(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            first_name:
                fake: first_name
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "first_name")

    @mock.patch(write_row_path)
    def test_fake_block_one_param(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            country:
                fake.country_code:
                    representation: alpha-2
        """
        generate(StringIO(yaml), {})
        assert len(row_values(write_row_mock, 0, "country")) == 2

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    @mock.patch(write_row_path)
    def test_fake_inline(self, write_row_mock, snowfakery_version):
        yaml = """
        - object: OBJ
          fields:
            country: ${{fake.country_code(representation='alpha-2')}}
        """
        generate(
            StringIO(yaml),
            {},
            plugin_options={"snowfakery_version": snowfakery_version},
        )
        assert len(row_values(write_row_mock, 0, "country")) == 2

    @mock.patch(write_row_path)
    def test_fake_inline_overrides(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            name: ${{fake.FirstName}} ${{fake.LastName}}
        """
        generate(StringIO(yaml), {}, None)
        assert len(row_values(write_row_mock, 0, "name").split(" ")) == 2

    @mock.patch(write_row_path)
    def test_fake_two_params_flat(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date: ${{fake.date(pattern="%Y-%m-%d", end_datetime=None)}}
        """
        generate(StringIO(yaml), {}, None)
        date = row_values(write_row_mock, 0, "date")
        assert type(date) == str, write_row_mock.mock_calls
        assert len(date.split("-")) == 3, date

    @mock.patch(write_row_path)
    def test_fake_two_params_nested(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date:
                fake.date_between:
                    start_date: -10y
                    end_date: today
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "date").year

    @mock.patch(write_row_path)
    def test_non_overlapping_dates(self, write_row_mock):
        yaml = """
        - object: OBJ
          fields:
            date:
                date_between:
                    start_date: today
                    end_date: 2000-01-01
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "date") is None

    def test_datetime_between(self, generated_rows):
        with open("tests/test_fake_datetimes.yml") as yaml:
            generate(yaml, {}, None)
            past = generated_rows.row_values(0, "past")
            future = generated_rows.row_values(0, "future")

            assert isinstance(past, datetime)
            assert isinstance(future, datetime)
            assert future > past  # Let's hope the future is greater

    def test_datetime_parsing(self, generated_rows):
        with open("tests/test_datetime.yml") as yaml:
            generate(yaml, {}, None)
            values = generated_rows.table_values("Datetimes")[0]
            assert values["also_right_now"].startswith("20")
            assert values["also_right_now"].endswith("+00:00")

    @mock.patch(write_row_path)
    def test_months_past(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            date:
              date_between:
                start_date: -4M
                end_date: -3M
        """
        generate(StringIO(yaml), {}, None)
        the_date = row_values(write_row_mock, 0, "date")
        assert (date.today() - the_date).days > 80
        assert (date.today() - the_date).days < 130

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_date_times(self, generated_rows, snowfakery_version):
        with open("tests/test_datetimes.yml") as yaml:
            generate(yaml, plugin_options={"snowfakery_version": snowfakery_version})

        for dt in generated_rows.table_values("Contact", field="EmailBouncedDate"):
            assert "+0" in dt or dt.endswith("Z"), dt
            assert dateparser.isoparse(dt).tzinfo

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_hidden_fakers(self, snowfakery_version):
        yaml = """
        - object: A
          fields:
            date:
              fake: DateTimeThisCentury
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(
                StringIO(yaml),
                plugin_options={"snowfakery_version": snowfakery_version},
            )

        assert e

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_bad_tz_param(self, snowfakery_version):
        yaml = """
        - object: A
          fields:
            date:
              fake.datetime:
                timezone: PST
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(
                StringIO(yaml),
                plugin_options={"snowfakery_version": snowfakery_version},
            )

        assert "timezone" in str(e.value)
        assert "relativedelta" in str(e.value)

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_no_timezone(self, generated_rows, snowfakery_version):
        yaml = """
        - object: A
          fields:
            date:
              fake.datetime:
                timezone: False
        """
        generate(
            StringIO(yaml),
            plugin_options={"snowfakery_version": snowfakery_version},
        )
        date = generated_rows.table_values("A", 0, "date")
        assert dateparser.isoparse(date).tzinfo is None

    @pytest.mark.parametrize("snowfakery_version", (2, 3))
    def test_relative_dates(self, generated_rows, snowfakery_version):
        with open("tests/test_relative_dates.yml") as f:
            generate(
                f,
                plugin_options={"snowfakery_version": snowfakery_version},
            )
        now = datetime.now(timezone.utc)
        # there is a miniscule chance that FutureDateTime picks a DateTime 1 second in the future
        # and then by the time we get here it isn't the future anymore. We'll see if it ever
        # happens in practice
        assert (
            dateparser.isoparse(generated_rows.table_values("Test", 1, "future")) >= now
        )
        assert (
            dateparser.isoparse(generated_rows.table_values("Test", 1, "future2"))
            >= now
        )
        assert (
            dateparser.isoparse(generated_rows.table_values("Test", 1, "past")) <= now
        )

    @mock.patch(write_row_path)
    def test_snowfakery_names(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            fn:
              fake: FirstName
            ln:
              fake: LastName
            un:
              fake: UserNAME
            un2:
              fake: username
            alias:
              fake: Alias
            email:
              fake: Email
            danger_mail:
              fake: RealisticMaybeRealEmail
            email2:
              fake: email
        """
        generate(StringIO(yaml), {}, None)
        assert "_" in row_values(write_row_mock, 0, "un")
        assert "@" in row_values(write_row_mock, 0, "un2")
        assert len(row_values(write_row_mock, 0, "alias")) <= 8
        assert "@example" in row_values(write_row_mock, 0, "email")
        assert "@" in row_values(write_row_mock, 0, "email2")
        assert "@" in row_values(write_row_mock, 0, "danger_mail")

    @mock.patch(write_row_path)
    def test_fallthrough_to_faker(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            SSN:
              fake: ssn
        """
        generate(StringIO(yaml), {}, None)
        assert row_values(write_row_mock, 0, "SSN")

    @mock.patch(write_row_path)
    def test_remove_underscores_from_faker(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            pn1:
              fake: PhoneNumber
            pn2:
              fake: phonenumber
            pn3:
              fake: phone_number
        """
        generate(StringIO(yaml), {}, None)
        assert set(row_values(write_row_mock, 0, "pn1")).intersection("0123456789")
        assert set(row_values(write_row_mock, 0, "pn2")).intersection("0123456789")
        assert set(row_values(write_row_mock, 0, "pn3")).intersection("0123456789")

    @mock.patch(write_row_path)
    def test_faker_kwargs(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            neg:
              fake.random_int:
                min: -5
                max: -1
        """
        generate(StringIO(yaml), {}, None)
        assert -5 <= row_values(write_row_mock, 0, "neg") <= -1

    @mock.patch(write_row_path)
    def test_error_handling(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            xyzzy:
              fake: xyzzy
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "xyzzy" in str(e.value)
        assert "fake" in str(e.value)

    @mock.patch(write_row_path)
    def test_did_you_mean(self, write_row_mock):
        yaml = """
        - object: A
          fields:
            xyzzy:
              fake: frst_name
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "first_name" in str(e.value)

    def test_faker_internals_are_invisible(self):
        yaml = """
        - object: A
          fields:
            xyzzy:
              fake: seed
        """
        with pytest.raises(exc.DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "seed" in str(e.value)

    def test_context_aware(self, generated_rows):
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
                Email:
                    fake: Email
            """
        generate(StringIO(yaml))
        assert generated_rows.table_values(
            "X", 0, "LastName"
        ) in generated_rows.table_values("X", 0, "Email")

    def test_context_username_incorporates_fakes(self, generated_rows):
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
                Username:
                    fake: Username
            """
        generate(StringIO(yaml))
        assert generated_rows.table_values(
            "X", 0, "FirstName"
        ) in generated_rows.table_values("X", 0, "Username")
        assert generated_rows.table_values(
            "X", 0, "LastName"
        ) in generated_rows.table_values("X", 0, "Username")

    def test_context_aware_multiple_values(self, generated_rows):
        yaml = """
            - object: X
              count: 3
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
                Email:
                    fake: Email
            """
        generate(StringIO(yaml))
        assert (
            generated_rows.table_values("X", 2)["LastName"]
            in generated_rows.table_values("X", 2)["Email"]
        )

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch("faker.providers.internet.en_US.Provider.ascii_safe_email")
    def test_context_aware_order_matters(self, email, first_name, generated_rows):
        yaml = """
            - object: X
              count: 3
              fields:
                Email:
                    fake: Email
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
            """
        generate(StringIO(yaml))
        assert first_name.mock_calls
        assert email.mock_calls

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch("faker.providers.internet.en_US.Provider.ascii_safe_email")
    def test_context_aware_no_leakage_count(self, email, first_name, generated_rows):
        yaml = """
            - object: X
              count: 3
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
                Email:
                    fake: Email
            """
        generate(StringIO(yaml))
        assert first_name.mock_calls
        assert not email.mock_calls

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch("faker.providers.internet.en_US.Provider.ascii_safe_email")
    def test_context_aware_no_leakage_templates(
        self, email, first_name, generated_rows
    ):
        # no leakage between templates
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: LastName
                Email:
                    fake: Email
            - object: Y
              fields:
                Email:
                    fake: Email
            """
        generate(StringIO(yaml))
        assert first_name.mock_calls
        email.assert_called_once()

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch("faker.providers.internet.en_US.Provider.ascii_safe_email")
    def test_context_aware_alernate_names(self, email, first_name, generated_rows):
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: first_name
                LastName:
                    fake: last_name
                Email:
                    fake: Email
            """
        generate(StringIO(yaml))
        assert first_name.mock_calls
        assert not email.mock_calls

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch("faker.providers.internet.en_US.Provider.ascii_safe_email")
    def test_disable_matching(self, email, first_name, generated_rows):
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: last_name
                Email: ${{fake.email(matching=False)}}
            """
        generate(StringIO(yaml))
        assert first_name.mock_calls
        assert email.mock_calls

    def test_emails_are_ascii(self, generated_rows):
        yaml = """
            - var: snowfakery_locale
              value: jp_JP
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: last_name
                Email:
                    fake: email
        """
        generate(StringIO(yaml))
        assert generated_rows.row_values(0, "Email").isascii()

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    @mock.patch(
        "snowfakery.fakedata.fake_data_generator.email_templates",
        ["{firstname}.{lastname}@{domain}"],
    )
    def test_emails_do_not_contain_spaces(self, first_name, generated_rows):
        yaml = """
            - object: X
              fields:
                FirstName:
                    fake: FirstName
                LastName:
                    fake: last_name
                Email:
                    fake: email
        """
        first_name.return_value = "A B C"
        generate(StringIO(yaml))
        assert " " not in generated_rows.row_values(0, "Email")
        assert "ABC" in generated_rows.row_values(0, "Email")

    @mock.patch("faker.providers.person.en_US.Provider.first_name")
    def test_username_length_limit(self, first_name, generated_rows):
        yaml = """
            - object: X
              fields:
                UserName:
                  fake: UserName
            """
        first_name.return_value = "A" * 100

        generate(StringIO(yaml))
        assert len(generated_rows.row_values(0, "UserName")) == 80, len(
            generated_rows.row_values(0, "UserName")
        )
