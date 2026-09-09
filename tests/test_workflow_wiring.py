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


def test_course_workflows_accept_utils_ref_and_use_local_utils_action():
    canvas_workflow = Path(".github/workflows/mdxcanvas_automation.yaml").read_text()
    docker_workflow = Path(".github/workflows/docker_automation.yaml").read_text()

    assert "utils_ref:" in canvas_workflow
    assert "utils_ref:" in docker_workflow
    assert "default: main" in canvas_workflow
    assert "default: main" in docker_workflow
    assert "ref: ${{ inputs.utils_ref }}" in canvas_workflow
    assert "ref: ${{ inputs.utils_ref }}" in docker_workflow
    assert "uses: ./utils/.github/actions/send-course-notification" in canvas_workflow
    assert "uses: ./utils/.github/actions/send-course-notification" in docker_workflow


def test_course_workflows_install_markdowndata_for_notification_formatting():
    canvas_workflow = Path(".github/workflows/mdxcanvas_automation.yaml").read_text()
    docker_workflow = Path(".github/workflows/docker_automation.yaml").read_text()

    # Order-insensitive: the two workflows list the same three packages in
    # different orders, and asserting on one literal spelling failed against
    # docker_automation.yaml, which installs tabulate first.
    for workflow in (canvas_workflow, docker_workflow):
        install = next(line for line in workflow.splitlines()
                       if "pip install" in line and "markdowndata" in line)
        for package in ("discord-webhook", "markdowndata", "tabulate"):
            assert package in install, install


def test_course_workflows_fail_the_job_when_the_work_step_failed():
    """A failed deploy or build must not leave a green check.

    Both workflows run their real work with `continue-on-error: true` so the
    Discord notification still goes out when it fails. That also makes the job
    succeed -- GitHub records the step's *conclusion* as success and only
    `outcome` remembers the failure -- so without a step like this one, a
    CS 312 deploy that threw halfway through reported success five times in a
    row while the course sat half-updated.
    """
    canvas_workflow = Path(".github/workflows/mdxcanvas_automation.yaml").read_text()
    docker_workflow = Path(".github/workflows/docker_automation.yaml").read_text()

    # outcome, not conclusion: conclusion is 'success' under continue-on-error
    assert "steps.mdxcanvas.outcome == 'failure'" in canvas_workflow
    assert "steps.run_build_dockers.outcome == 'failure'" in docker_workflow

    # and the notification must still be sent on the failing path
    assert "if: always()" in canvas_workflow
    assert "if: always()" in docker_workflow


def test_the_failure_check_runs_after_the_notification():
    """Ordering is the whole point: re-failing before the notification step
    would trade a wrong green check for a missing Discord message."""
    for name, step in (("mdxcanvas_automation.yaml", "Fail the job if MDXCanvas failed"),
                       ("docker_automation.yaml",
                        "Fail the job if the Docker build failed")):
        text = Path(f".github/workflows/{name}").read_text()
        assert text.index("Send course notification") < text.index(step), name
