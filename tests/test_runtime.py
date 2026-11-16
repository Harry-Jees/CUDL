import pytest

from cudl.runtime import CUDLRuntimeError, run_script


def test_variables_are_dynamically_typed_and_can_be_interpolated():
    result = run_script(
        "script\n"
        "    #value = 21\n"
        "    #value = Harry\n"
        "    #message = Welcome #value\n"
        "    print #message\n"
    )

    assert result.variables["value"] == "Harry"
    assert result.variables["message"] == "Welcome Harry"
    assert result.output == ["Welcome Harry"]


def test_at_functions_accept_arguments_and_return_computed_values():
    result = run_script(
        "script\n"
        "    @greet #person\n"
        "        print Hello #person\n"
        "    @add #left #right\n"
        "        return #left + #right\n"
        "    @greet Harry Jees\n"
        "    #total = @add 10 20\n"
        "    print #total\n"
    )

    assert result.output == ["Hello Harry Jees", "30"]
    assert result.variables["total"] == 30
    assert isinstance(result.variables["total"], int)


def test_hash_paths_support_mapping_and_sequence_indexing():
    result = run_script(
        "script\n"
        "    #first = #users[0].profile[name]\n"
        "    print #first\n",
        data={"users": [{"profile": {"name": "Ada"}}]},
    )

    assert result.variables["first"] == "Ada"
    assert result.output == ["Ada"]


def test_list_and_mapping_literals_support_simple_indexing():
    result = run_script(
        "script\n"
        "    #items = [Harry, Ada, Lin]\n"
        "    #user = {name: Harry, age: 21}\n"
        "    #first = #items[0]\n"
        "    #person = #user[name]\n"
        "    print #first\n"
        "    print #person\n"
    )

    assert result.variables["items"] == ["Harry", "Ada", "Lin"]
    assert result.variables["user"] == {"name": "Harry", "age": 21}
    assert result.output == ["Harry", "Harry"]


def test_safe_arithmetic_and_comparisons_are_evaluated():
    result = run_script(
        "script\n"
        "    #score = 10 + 5 * 2\n"
        "    #passed = #score >= 20\n"
        "    #label = #passed and true\n"
        "    print #score\n"
        "    print #label\n"
    )

    assert result.variables["score"] == 20
    assert result.variables["passed"] is True
    assert result.variables["label"] is True
    assert result.output == ["20", "True"]


def test_constants_cannot_be_reassigned():
    with pytest.raises(CUDLRuntimeError, match="cannot be reassigned"):
        run_script(
            "script\n"
            "    const #limit = 10\n"
            "    #limit = 20\n"
        )


def test_runtime_does_not_execute_python_or_arbitrary_expression_calls():
    result = run_script(
        "python\n"
        "    import os\n"
        "    os.remove('important-file')\n"
        "script\n"
        "    #value = 1\n"
    )
    assert result.variables["value"] == 1

    with pytest.raises(CUDLRuntimeError, match="Unsupported expression element"):
        run_script(
            "script\n"
            "    #value = #number + __import__('os').system('echo unsafe')\n",
            data={"number": 1},
        )


def test_unknown_functions_and_wrong_argument_counts_are_reported():
    with pytest.raises(CUDLRuntimeError, match="Unknown function"):
        run_script("script\n    @missing Harry\n")

    with pytest.raises(CUDLRuntimeError, match="expects 2 argument"):
        run_script(
            "script\n"
            "    @add #left #right\n"
            "        return #left + #right\n"
            "    @add 10\n"
        )
