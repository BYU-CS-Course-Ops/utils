from pathlib import Path


def test_send_course_notification_action_wires_course_metadata_and_short_branch():
    text = Path(".github/actions/send-course-notification/action.yml").read_text()

    assert "course-name:" in text
    assert "course-url:" in text
    assert '--course-name "${{ inputs.course-name }}"' in text
    assert '--course-url "${{ inputs.course-url }}"' in text
    assert '--branch "${{ github.ref_name }}"' in text


def test_course_workflows_expose_and_forward_course_metadata_inputs():
    canvas_workflow = Path(".github/workflows/mdxcanvas_automation.yaml").read_text()
    docker_workflow = Path(".github/workflows/docker_automation.yaml").read_text()

    assert "course_name:" in canvas_workflow
    assert "course_url:" in canvas_workflow
    assert "course-name: ${{ inputs.course_name }}" in canvas_workflow
    assert "course-url: ${{ inputs.course_url }}" in canvas_workflow

    assert "course_name:" in docker_workflow
    assert "course_url:" in docker_workflow
    assert "course-name: ${{ inputs.course_name }}" in docker_workflow
    assert "course-url: ${{ inputs.course_url }}" in docker_workflow
