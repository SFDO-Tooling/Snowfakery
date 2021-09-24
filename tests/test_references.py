from io import StringIO
from unittest import mock

import pytest

from snowfakery.data_generator import generate
from test_parse_samples import find_row
from snowfakery.data_gen_exceptions import DataGenError
from snowfakery.api import StoppingCriteria

simple_parent = """                     #1
- object: A                             #2
  fields:                               #3
    B:                                  #4
        object: B                       #5
        fields:                         #6
            A_ref:                      #7
                reference: A            #8
    """

simple_parent_list = """                #1
- object: A                             #2
  fields:                               #3
    B:                                  #4
      - object: B                       #5
        fields:                         #6
            A_ref:                      #7
                reference: A            #8
    """


ancestor_reference = """                #1
- object: A                             #2
  fields:                               #3
    B:                                  #4
      - object: B                       #5
        fields:                         #6
            C:                          #7
               object: C                #8
               fields:                  #9
                  A_ref:                #10
                     reference: A       #11
    """

reference_from_friend = """             #1
- object: A                             #2
  friends:                              #3
      - object: B                       #4
        fields:                         #5
            A_ref:                      #6
                reference: A            #7
    """

write_row_path = "snowfakery.output_streams.DebugOutputStream.write_single_row"


class TestReferences:
    @mock.patch(write_row_path)
    def test_simple_parent(self, write_row):
        generate(StringIO(simple_parent), {}, None)

        a_values = find_row("A", {}, write_row.mock_calls)
        b_values = find_row("B", {}, write_row.mock_calls)
        id_a = a_values["id"]
        reference_b = a_values["B"]
        id_b = b_values["id"]
        reference_a = b_values["A_ref"]
        assert f"A({id_a})" == reference_a
        assert f"B({id_b})" == reference_b

    @mock.patch(write_row_path)
    def test_simple_parent_list_child(self, write_row):
        generate(StringIO(simple_parent_list), {}, None)

        a_values = find_row("A", {}, write_row.mock_calls)
        b_values = find_row("B", {}, write_row.mock_calls)
        id_a = a_values["id"]
        reference_b = a_values["B"]
        id_b = b_values["id"]
        reference_a = b_values["A_ref"]
        assert f"A({id_a})" == reference_a
        assert f"B({id_b})" == reference_b

    @mock.patch(write_row_path)
    def test_ancestor_reference(self, write_row):
        generate(StringIO(ancestor_reference), {}, None)

        a_values = find_row("A", {}, write_row.mock_calls)
        c_values = find_row("C", {}, write_row.mock_calls)
        id_a = a_values["id"]
        reference_a = c_values["A_ref"]
        assert f"A({id_a})" == reference_a

    @mock.patch(write_row_path)
    def test_reference_from_friend(self, write_row):
        generate(StringIO(reference_from_friend), {}, None)

        a_values = find_row("A", {}, write_row.mock_calls)
        b_values = find_row("B", {}, write_row.mock_calls)
        id_a = a_values["id"]
        reference_a = b_values["A_ref"]
        assert f"A({id_a})" == reference_a

    @mock.patch(write_row_path)
    def test_forward_reference(self, write_row):
        yaml = """
        - object: A
          fields:
            B:
              reference: Bob
        - object: B
          nickname: Bob
          fields:
            A:
              reference: A
        """
        generate(StringIO(yaml), {}, None)

        a_values = find_row("A", {}, write_row.mock_calls)
        b_values = find_row("B", {}, write_row.mock_calls)
        assert a_values["B"] == "B(1)"
        assert b_values["A"] == "A(1)"

    @mock.patch(write_row_path)
    def test_forward_reference__tablename(self, write_row):
        yaml = """
            - object: A
              fields:
                B:
                  reference:
                    B
            - object: B
              fields:
                A:
                  reference:
                    A
              """
        generate(StringIO(yaml), {}, None)
        a_values = find_row("A", {}, write_row.mock_calls)
        b_values = find_row("B", {}, write_row.mock_calls)
        assert a_values["B"] == "B(1)"
        assert b_values["A"] == "A(1)"

    @mock.patch(write_row_path)
    def test_forward_reference_not_fulfilled(self, write_row):
        yaml = """
        - object: A
          fields:
            B:
              reference: Bob
        - object: B
          count: 0
          nickname: Bob
          fields:
            A:
              reference: A
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)

        assert "Bob" in str(e.value)

    def test_forward_reference_not_fulfilled__tablename(self):
        yaml = """
            - object: AAA
              fields:
                B:
                  reference:
                    BBB
            - object: BBB
              count: 0
              fields:
                A:
                  reference:
                    AAA
              """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "BBB" in str(e.value)

    @mock.patch(write_row_path)
    def test_forward_references_not_fulfilled__nickname(self, write_row):
        yaml = """
        - object: A
          fields:
            B:
              reference: Bob
            C:
              reference: Bill
        - object: B
          count: 0
          nickname: Bob
          fields:
            A:
              reference: A
        - object: B
          count: 0
          nickname: Bill
          fields:
            A:
              reference: A
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)

        assert "Bob" in str(e.value)
        assert "Bill" in str(e.value)

    def test_dotted_references(self, generated_rows):
        yaml = """
        - object: A
          fields:
            num: 5
        - object: B
          fields:
            A:
              reference: A
        - object: C
          fields:
            BRef:
              reference: B
            D:
              reference: BRef.A
        """
        generate(StringIO(yaml), {}, None)
        assert generated_rows.row_values(2, "D") == "A(1)"

    def test_dotted_references_broken(self, generated_rows):
        yaml = """
        - object: A
          fields:
            num: 5
        - object: B
          fields:
            A:
              reference: A
        - object: C
          fields:
            BRef:
              reference: B
            D:
              reference: QQQ.A
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "QQQ.A" in str(e.value)

    def test_dotted_references_broken_2(self, generated_rows):
        yaml = """
        - object: A
          fields:
            num: 5
        - object: B
          fields:
            A:
              reference: A
        - object: C
          fields:
            BRef:
              reference: B
            D:
              reference: BRef.QQQ
        """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml), {}, None)
        assert "BRef.QQQ" in str(e.value)

    def test_forward_reference__iterations(self, generated_rows):
        yaml = """
            - object: A
              fields:
                B_ref:
                  reference:
                    B
            - object: B
              fields:
                A_ref:
                  reference:
                    A
              """
        generate(StringIO(yaml), {}, stopping_criteria=StoppingCriteria("A", 3))
        assert generated_rows.mock_calls == [
            mock.call("A", {"id": 1, "B_ref": "B(1)"}),
            mock.call("B", {"id": 1, "A_ref": "A(1)"}),
            mock.call("A", {"id": 2, "B_ref": "B(2)"}),
            mock.call("B", {"id": 2, "A_ref": "A(2)"}),
            mock.call("A", {"id": 3, "B_ref": "B(3)"}),
            mock.call("B", {"id": 3, "A_ref": "A(3)"}),
        ]

    def _generate_loop(self, yaml, iterations, num_per_iteration):
        old_continuation_data = None
        for i in range(0, iterations):
            continuation_file = StringIO()
            generate(
                StringIO(yaml),
                {},
                stopping_criteria=StoppingCriteria("A", num_per_iteration),
                continuation_file=old_continuation_data,
                generate_continuation_file=continuation_file,
            )
            old_continuation_data = StringIO(continuation_file.getvalue())

    def test_forward_reference__nickname__iterations(self, generated_rows):
        yaml = """
            - object: A
              fields:
                B_ref:
                  reference:
                    B_nick
            - object: B
              nickname: B_nick
              fields:
                A_ref:
                  reference:
                    A
              """
        self._generate_loop(yaml, 3, 2)

        assert generated_rows.mock_calls == [
            mock.call("A", {"id": 1, "B_ref": "B(1)"}),
            mock.call("B", {"id": 1, "A_ref": "A(1)"}),
            mock.call("A", {"id": 2, "B_ref": "B(2)"}),
            mock.call("B", {"id": 2, "A_ref": "A(2)"}),
            mock.call("A", {"id": 3, "B_ref": "B(3)"}),
            mock.call("B", {"id": 3, "A_ref": "A(3)"}),
            mock.call("A", {"id": 4, "B_ref": "B(4)"}),
            mock.call("B", {"id": 4, "A_ref": "A(4)"}),
            mock.call("A", {"id": 5, "B_ref": "B(5)"}),
            mock.call("B", {"id": 5, "A_ref": "A(5)"}),
            mock.call("A", {"id": 6, "B_ref": "B(6)"}),
            mock.call("B", {"id": 6, "A_ref": "A(6)"}),
        ]

    def test_forward_reference__iterations__with_just_once(self, generated_rows):
        yaml = """
            - object: A
              fields:
                B_ref:
                  reference:
                    B_nick
            - object: B
              just_once: True
              nickname: B_nick
              fields:
                A_ref:
                  reference:
                    A
              """
        self._generate_loop(yaml, 3, 2)
        assert generated_rows.mock_calls == [
            mock.call("A", {"id": 1, "B_ref": "B(1)"}),
            mock.call("B", {"id": 1, "A_ref": "A(1)"}),
            mock.call("A", {"id": 2, "B_ref": "B(1)"}),
            mock.call("A", {"id": 3, "B_ref": "B(1)"}),
            mock.call("A", {"id": 4, "B_ref": "B(1)"}),
            mock.call("A", {"id": 5, "B_ref": "B(1)"}),
            mock.call("A", {"id": 6, "B_ref": "B(1)"}),
        ]

    def test_random_reference_simple(self, generated_rows):
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #4
      - object: B                   #5
        count: 2                    #6
        fields:                     #7
            A_ref:                  #8
              random_reference: A   #9
    """
        with mock.patch("random.randint") as randint:
            randint.side_effect = [8, 3]
            generate(StringIO(yaml))
        assert generated_rows.row_values(10, "A_ref") == "A(8)"
        assert generated_rows.row_values(11, "A_ref") == "A(3)"

    def test_random_reference_local(self, generated_rows):
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #4
      - object: B                   #5
        fields:                     #7
            A_ref:                  #8
              random_reference:     #9
                tablename: A        #10
                scope: current-iteration        #11
    """
        with mock.patch("random.randint") as randint:
            randint.side_effect = [8, 12]
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("B", 2))
            assert randint.mock_calls == [mock.call(1, 10), mock.call(11, 20)]
        assert generated_rows.table_values("B", 2, "A_ref") == "A(12)"

    def test_random_reference_global(self, generated_rows):
        # undocumented experimental feature!
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #4
      - object: B                   #5
        count: 2                    #6
        fields:                     #7
            A_ref:                  #8
              random_reference:
                tablename: A   #9
                scope: prior-and-current-iterations
    """
        with mock.patch("random.randint") as randint, mock.patch(
            "warnings.warn"
        ) as warn:
            randint.side_effect = [8, 3, 8, 3]
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("B", 4))
        assert generated_rows.row_values(22, "A_ref") == "A(8)"
        assert generated_rows.row_values(23, "A_ref") == "A(3)"
        assert "experimental" in str(warn.mock_calls)

    def test_random_reference_missing_table(self):
        yaml = """                  #1
      - object: A                   #2
        count: 2                    #3
        fields:                     #4
            A_ref:                  #5
              random_reference:
                tablename: B
    """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "There is no table named B" in str(e)

    def test_random_reference_wrong_scope(self):
        # undocumented experimental feature!
        yaml = """                  #1
      - object: A                   #2
      - object: B                   #3
        count: 2                    #4
        fields:                     #5
            A_ref:                  #6
              random_reference:
                tablename: A
                scope: xyzzy
    """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "Scope must be" in str(e)

    def test_random_reference_to_nickname(self):
        # undocumented experimental feature!
        yaml = """
      - object: A
        nickname: AA
      - object: B
        count: 2
        fields:
            A_ref:
              random_reference: AA
    """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "nickname" in str(e).lower()

    def test_reference_unknown_object(self):
        yaml = """
        - object: B
          count: 2
          fields:
              A_ref:
                reference: AA"""
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "cannot find" in str(e).lower()

    def test_reference_wrong_type(self):
        yaml = """
        - object: B
          count: 2
          fields:
              __foo: 5
              A_ref:
                reference: __foo"""
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "incorrect object type" in str(e).lower()

    def test_reference_really_wrong_type(self):
        yaml = """
        - object: B
          count: 2
          fields:
              A_ref:
                reference: 5"""
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "can't get reference to object" in str(e).lower()

    def test_random_reference_to_just_once_obj(self, generated_rows):
        yaml = """
              - object: Parent
                just_once: true

              - object: Child
                fields:
                  parent:
                    random_reference: Parent
                """
        generate(StringIO(yaml), stopping_criteria=StoppingCriteria("Child", 2))
        assert len(generated_rows.mock_calls) == 3

    def test_random_reference_to_nickname_fails(self):
        yaml = """
              - object: Parent
                nickname: ParentNickname
                just_once: true

              - object: Child
                fields:
                  parent:
                    random_reference: ParentNickname
                """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "there is no table named parent" in str(e).lower()
