from datetime import date
from io import StringIO
from unittest import mock
import dateutil

import pytest
from test_parse_samples import find_row

from snowfakery.api import StoppingCriteria
from snowfakery.data_gen_exceptions import DataGenError, DataGenSyntaxError
from snowfakery.data_generator import generate

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

    def test_reference_by_id(self, generated_rows):
        yaml = """
              - object: Parent
                nickname: ParentNickname
                just_once: true

              - object: Child
                fields:
                  parent1:
                    reference: ParentNickname
                  parent2:
                    reference:
                      object: Parent
                      id: 1
                """

        generate(StringIO(yaml))
        child = generated_rows.table_values("Child", 0)
        assert child["parent1"] == child["parent2"]


class TestRandomReferencesOriginal:
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
        with mock.patch("snowfakery.row_history.randint") as randint:
            randint.side_effect = [8, 3]
            generate(StringIO(yaml))
        assert generated_rows.row_values(10, "A_ref") == "A(8)"
        assert generated_rows.row_values(11, "A_ref") == "A(3)"

    def test_random_reference_alternate_syntax(self, generated_rows):
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #4
      - object: B                   #5
        count: 2                    #6
        fields:                     #7
            A_ref:                  #8
              random_reference:     #9
                to: A               #10
    """
        with mock.patch("snowfakery.row_history.randint") as randint:
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
                to: A        #10
                scope: current-iteration        #11
    """
        with mock.patch("snowfakery.row_history.randint") as randint:
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
                to: A   #9
                scope: prior-and-current-iterations
    """
        with mock.patch("snowfakery.row_history.randint") as randint, mock.patch(
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
                to: B
    """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "There is no table or nickname `B`" in str(e)

    def test_random_reference_wrong_scope(self):
        # undocumented experimental feature!
        yaml = """                  #1
      - object: A                   #2
      - object: B                   #3
        count: 2                    #4
        fields:                     #5
            A_ref:                  #6
              random_reference:
                to: A
                scope: xyzzy
    """
        with pytest.raises(DataGenError) as e:
            generate(StringIO(yaml))
        assert "Scope must be" in str(e)

    def test_random_reference__type_error(self, generated_rows):
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #4
      - object: B                   #5
        count: 2                    #6
        fields:                     #7
            A_ref:                  #8
              random_reference:  5   #9
    """
        with pytest.raises(DataGenSyntaxError):
            generate(StringIO(yaml))


class TestRandomReferencesNew:
    # New tests

    def test_random_reference_to_just_once_obj(self, generated_rows):
        yaml = """
              - object: Parent
                just_once: true

              - object: Child
                fields:
                  parent:
                    random_reference: Parent
                """
        generate(StringIO(yaml), stopping_criteria=StoppingCriteria("Child", 3))
        assert len(generated_rows.mock_calls) == 4

    @pytest.mark.parametrize("rand_top", [True, False])
    def test_random_reference_to_just_once_obj_many(self, generated_rows, rand_top):
        yaml = """
              - object: Parent
                count: 3
                just_once: true
              - object: Parent
                count: 3
                just_once: true

              - object: Child
                fields:
                  parent:
                    random_reference: Parent
                """

        def randint_mock(x, y):
            return y if rand_top else x

        with mock.patch("snowfakery.row_history.randint", randint_mock):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("Child", 2))
        if rand_top:
            assert generated_rows.table_values("Child", 1, "parent") == "Parent(6)"
        else:
            assert generated_rows.table_values("Child", 1, "parent") == "Parent(1)"

    @pytest.mark.parametrize("rand_top", [True, False])
    def test_random_reference_to_just_once_obj_and_local(
        self, generated_rows, rand_top
    ):
        yaml = """
              - object: Parent
                count: 3
                just_once: true

              - object: Parent
                count: 3

              - object: Child
                fields:
                  parent:
                    random_reference: Parent
                """

        def randint_mock(x, y):
            return y if rand_top else x

        with mock.patch("snowfakery.row_history.randint", randint_mock):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("Child", 3))
        FIRST, LAST = 1, -1
        if rand_top:
            assert generated_rows.table_values("Child", FIRST, "parent") == "Parent(6)"
            assert generated_rows.table_values("Child", LAST, "parent") == "Parent(12)"
        else:  # bottom
            assert generated_rows.table_values("Child", FIRST, "parent") == "Parent(1)"
            assert generated_rows.table_values("Child", LAST, "parent") == "Parent(10)"

    @pytest.mark.parametrize("rand_top", [True, False])
    def test_random_reference_to_just_once_nickname_succeeds(
        self, generated_rows, rand_top
    ):
        yaml = """
              - object: Parent
                nickname: ParentNickname
                count: 3
                just_once: true

              - object: Child
                fields:
                  parent:
                    random_reference: ParentNickname
                """

        def randint_mock(x, y):
            return y if rand_top else x

        with mock.patch("snowfakery.row_history.randint", randint_mock):
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("Child", 3))
        FIRST, LAST = 1, -1
        if rand_top:
            assert generated_rows.table_values("Child", FIRST, "parent") == "Parent(3)"
            assert generated_rows.table_values("Child", LAST, "parent") == "Parent(3)"
        else:  # bottom
            assert generated_rows.table_values("Child", FIRST, "parent") == "Parent(1)"
            assert generated_rows.table_values("Child", LAST, "parent") == "Parent(1)"

    def test_random_reference_to_nickname(self, generated_rows):
        yaml = """
      - object: A
        nickname: AA
      - object: B
        count: 2
        fields:
            A_ref:
              random_reference: AA
    """
        generate(StringIO(yaml))
        assert generated_rows.table_values("B", 2, "A_ref") == "A(1)"

    def test_random_reference_to_nickname_sparse(self, generated_rows):
        yaml = """
      - object: A
        count: 5
      - object: A
        nickname: nicky
        count: 2
        fields:
            name: nicky
      - object: A
        count: 5
      - object: B
        count: 3
        fields:
            nicky_ref:
              random_reference: nicky
            nicky_name: ${{nicky_ref.name}}
    """
        generate(StringIO(yaml))
        assert generated_rows.table_values("B", 2, "nicky_name") == "nicky"

    def test_forward_random_reference_nickname_fails(self):
        yaml = """
              - object: Child
                fields:
                  parent1:
                    random_reference: ParentNickname

              - object: Parent
                count: 10
                nickname: ParentNickname
                """
        with pytest.raises(
            DataGenError,
            match="There is no table or nickname `ParentNickname` at this point in the recipe.",
        ):
            generate(StringIO(yaml))

    def test_forward_random_reference_object_fails(self):
        yaml = """
              - object: Child
                fields:
                  parent1:
                    random_reference: Parent

              - object: Parent
                count: 10
                """
        with pytest.raises(
            DataGenError,
            match="There is no table or nickname `Parent` at this point in the recipe.",
        ):
            generate(StringIO(yaml))

    def test_random_reference_to_just_once_object(self, generated_rows):
        yaml = """
      - object: A
        count: 3
        just_once: True
      - object: B
        count: 2
        fields:
            A_ref:
              random_reference: A
    """
        with mock.patch("snowfakery.row_history.randint") as randint:
            randint.side_effect = [1, 2]
            generate(StringIO(yaml))
            assert randint.mock_calls == [mock.call(1, 3), mock.call(1, 3)]
        assert generated_rows.table_values("B", 1, "A_ref") == "A(1)"
        assert generated_rows.table_values("B", 2, "A_ref") == "A(2)"

    def test_random_reference_to_just_once_nickname(self, generated_rows):
        yaml = """
      - object: A
        count: 3
        nickname: AA
        just_once: True
      - object: B
        count: 2
        fields:
            A_ref:
              random_reference: AA
    """
        with mock.patch("snowfakery.row_history.randint") as randint:
            randint.side_effect = [2, 1]
            generate(StringIO(yaml))
        assert generated_rows.table_values("B", 1, "A_ref") == "A(2)"
        assert generated_rows.table_values("B", 2, "A_ref") == "A(1)"

    def test_random_reference_to_nickname__subsequent_iterations(self, generated_rows):
        yaml = """
      - object: A
        just_once: True
      - object: A
      - object: A
        nickname: nicky
        fields:
          name: nicky
      - object: B
        count: 2
        fields:
            A_ref:
              random_reference: nicky
            nameref: ${{A_ref.name}}
    """
        with mock.patch("snowfakery.row_history.randint") as randint:
            randint.side_effect = lambda x, y: x
            generate(StringIO(yaml), stopping_criteria=StoppingCriteria("B", 10))
        assert generated_rows.table_values("B", 10, "A_ref") == "A(11)"
        assert generated_rows.table_values("B", 10, "nameref") == "nicky"

    def test_random_reference__properties(self, generated_rows):
        yaml = """
              - object: GrandParent
                fields:
                  name: Pappy

              - object: Parent
                fields:
                  parent:
                    reference:
                      GrandParent

              - object: Child
                fields:
                  pa:
                    random_reference: Parent
                  paps: ${{pa.parent.name}}
                """
        generate(StringIO(yaml))
        assert generated_rows.table_values("Child", 1, "paps") == "Pappy"

    def test_random_reference__weird_type_properties(self, generated_rows):
        # unusual types are not serialized and won't be returned
        yaml = """
              - plugin: tests.test_custom_plugins_and_providers.EvalPlugin
              - object: Parent
                nickname: parent_with_counter
                fields:
                  add:
                    EvalPlugin.add:
                      - 2
                      - 3

              - object: Child
                fields:
                  pa:
                    random_reference: parent_with_counter
                  weird: ${{pa.add}}
                """
        generate(StringIO(yaml))
        assert str(generated_rows.table_values("Child", 1, "weird")).startswith(
            "Type_Cannot_Be_Used_With_Random_Reference"
        )

    def test_deep_random_references__by_tablename(self, generated_rows):
        yaml = """
              - object: GrandParent
                count: 3
                fields:
                  name: mammy

              - object: Parent
                fields:
                  ma:
                    random_reference: GrandParent

              - object: Child
                fields:
                  gamma:
                    random_reference: Parent
                  mamma_name: ${{gamma.ma.name}}
                """
        generate(StringIO(yaml))
        assert generated_rows.table_values("Child", 1, "mamma_name") == "mammy"

    def test_deep_random_references__by_nickname(self, generated_rows):
        yaml = """
              - object: GrandParent
                nickname: mammy
                count: 3
                fields:
                  name: mammy

              - object: Parent
                nickname: par
                fields:
                  ma:
                    random_reference: mammy

              - object: Child
                fields:
                  gamma:
                    random_reference: par
                  mamma_name: ${{gamma.ma.name}}
                """
        generate(StringIO(yaml))
        assert generated_rows.table_values("Child", 1, "mamma_name") == "mammy"

    def test_random_reference__with_continuation(
        self, generate_data_with_continuation, generated_rows
    ):
        yaml = """                  #1
      - object: A                   #2
        count: 10                   #3
      - object: B                   #4
        count: 5                    #5
        fields:                     #6
            A_ref:                  #7
              random_reference:     #8
                to: A               #9
    """
        generate_data_with_continuation(
            yaml=yaml,
            target_number=("B", 5),
            times=3,
        )

        def parseref(reference):
            return int(reference.split("(")[1].strip(")"))

        last_five_Bs = generated_rows.table_values("B")[-5:]
        referenced_As = [parseref(b["A_ref"]) for b in last_five_Bs]
        assert all(a >= 20 for a in referenced_As), referenced_As

    def test_random_reference_to_objects_with_diverse_types(self, generated_rows):
        # There is a risk that some weird types will not be serialized
        # correctly.
        yaml = """
      - object: A
        count: 3
        nickname: AA
        fields:
          date: 2022-01-01
          date2: ${{today}}
          date3:
            date_between:
              start_date: 2000-01-01
              end_date: today
          decimal:
            fake: latitude
          datetime1:
            fake: datetime
          datetime2: ${{now}}
      - object: B
        fields:
            A_ref:
              random_reference: AA
            date1ref: ${{A_ref.date}}
            date2ref: ${{A_ref.date2}}
            date3ref: ${{A_ref.date3}}
            decimalref: ${{A_ref.decimal}}
            datetime1ref: ${{A_ref.datetime1}}
            datetime2ref: ${{A_ref.datetime2}}
    """

        parse_date = dateutil.parser.parse

        generate(StringIO(yaml))
        assert generated_rows.table_values("B", 1, "date1ref") == "2022-01-01"
        assert date.fromisoformat(generated_rows.table_values("B", 1, "date2ref"))
        assert date.fromisoformat(generated_rows.table_values("B", 1, "date3ref"))
        assert float(generated_rows.table_values("B", 1, "decimalref"))
        assert parse_date(generated_rows.table_values("B", 1, "datetime1ref"))
        assert parse_date(generated_rows.table_values("B", 1, "datetime2ref"))

    def test_random_references__nested(self, generated_rows):
        yaml = """
      - object: Parent
        count: 2
        fields:
          child1:
            - object: Child1
              fields:
                child2:
                  - object: Child2
                    fields:
                      name: TheName
      - object: Child3
        fields:
            A_ref:
              random_reference:
                to: Parent
            nested_name:
              ${{A_ref.child1.child2.name}}
    """
        generate(StringIO(yaml))
        assert generated_rows.table_values("Child3", 1, "nested_name") == "TheName"
        assert generated_rows.table_values("Child3", -1, "nested_name") == "TheName"

    def test_random_references__nested__with_continuation(
        self, generate_data_with_continuation, generated_rows
    ):
        yaml = """
      - object: Parent
        count: 2
        fields:
          child1:
            - object: Child1
              fields:
                child2:
                  - object: Child2
                    fields:
                      name: TheName
      - object: Child3
        fields:
            A_ref:
              random_reference:
                to: Parent
            nested_name:
              ${{A_ref.child1.child2.name}}
    """
        generate_data_with_continuation(
            yaml=yaml,
            target_number=("Parent", 4),
            times=1,
        )
        assert generated_rows.table_values("Child3", 1, "nested_name") == "TheName"
        assert generated_rows.table_values("Child3", -1, "nested_name") == "TheName"
