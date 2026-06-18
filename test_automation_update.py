from pathlib import Path

from backend.exporter import _get_pages_url


ROOT = Path(__file__).parent


def test_weekly_workflow_exports_and_publishes_report():
    workflow = (ROOT / ".github" / "workflows" / "weekly-crawl.yml").read_text()

    assert "export_to_html" in workflow
    assert "reports/" in workflow
    assert "git push origin main" in workflow


def test_deploy_script_uses_standalone_crawl_job():
    deploy_script = (ROOT / "deploy.sh").read_text()

    assert "python3 scripts/crawl_job.py" in deploy_script
    assert "backend/main.py --trigger" not in deploy_script


def test_pages_url_uses_environment_when_dotenv_config_is_absent(monkeypatch):
    monkeypatch.setenv("GITHUB_USERNAME", "bonnycho98-hub")
    monkeypatch.setenv("GITHUB_REPO_NAME", "job-report")

    assert _get_pages_url({}) == "https://bonnycho98-hub.github.io/job-report"
