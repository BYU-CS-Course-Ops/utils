"""Deriving the course id and URL from a course-info file.

The five courses on these workflows do not share a schema. CS 235's file is
JSON; the rest are YAML, with varied spacing and quoting. All five agree on the
two top-level keys this reads, which is why only those two are derived -- the
course name is not, and stays an input.
"""
from pathlib import Path

import pytest

from notifications.course_facts import CourseFactsError, course_facts


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "course-info"
    path.write_text(text)
    return path


def test_yaml_as_four_of_the_five_courses_write_it(tmp_path):
    path = write(tmp_path, """
CANVAS_API_URL : https://byu.instructure.com/
CANVAS_COURSE_ID : 38614
LOCAL_TIME_ZONE : America/Denver
GLOBAL_ARGS:
  COURSE_SETTINGS:
    <course-settings name='CS 312' code='CS 312 (F26)'/>
""")
    assert course_facts(path) == {
        "course_id": "38614",
        "course_url": "https://byu.instructure.com/courses/38614",
    }


def test_json_as_cs235_writes_it(tmp_path):
    """JSON is valid YAML, so one parser covers both. CS 235 is the only one."""
    path = write(tmp_path, """
{
    "CANVAS_API_URL": "https://byu.instructure.com/",
    "CANVAS_COURSE_ID": 34963,
    "GLOBAL_ARGS": {"COURSE_NAME": "C S 235: Data Structures (Fall 2026)"}
}
""")
    assert course_facts(path)["course_url"] == "https://byu.instructure.com/courses/34963"


def test_an_api_url_without_a_trailing_slash_does_not_double_it(tmp_path):
    """Every file has the slash today. The first one that does not should still
    produce a working URL rather than .../courses//123."""
    path = write(tmp_path, "CANVAS_API_URL: https://byu.instructure.com\n"
                           "CANVAS_COURSE_ID: 123\n")
    assert course_facts(path)["course_url"] == "https://byu.instructure.com/courses/123"


def test_a_numeric_id_comes_back_as_a_string(tmp_path):
    """YAML gives an int, JSON gives an int; the workflow needs text."""
    path = write(tmp_path, "CANVAS_API_URL: https://x/\nCANVAS_COURSE_ID: 7\n")
    assert course_facts(path)["course_id"] == "7"


@pytest.mark.parametrize("text, missing", [
    ("CANVAS_API_URL: https://x/\n", "CANVAS_COURSE_ID"),
    ("CANVAS_COURSE_ID: 7\n", "CANVAS_API_URL"),
])
def test_a_missing_key_names_itself(tmp_path, text, missing):
    """The caller has to know which key to add, not merely that something failed."""
    with pytest.raises(CourseFactsError, match=missing):
        course_facts(write(tmp_path, text))


def test_a_file_that_is_not_a_mapping_is_an_error(tmp_path):
    with pytest.raises(CourseFactsError):
        course_facts(write(tmp_path, "- just\n- a list\n"))


def test_unparseable_content_is_an_error_not_a_crash(tmp_path):
    with pytest.raises(CourseFactsError):
        course_facts(write(tmp_path, "key: [unclosed\n"))
