import json
from pathlib import Path

from eca_reference.cli import main
from tests.factories import make_contract


def test_cli_validates_contract_and_prints_phase_report(tmp_path, capsys):
    path = tmp_path / "contract.json"
    path.write_text(json.dumps(make_contract()), encoding="utf-8")
    code = main([str(path), "--phase", "PRE", "--now", "2026-11-18T12:00:00Z"])
    captured = capsys.readouterr()
    assert code == 0
    result = json.loads(captured.out)
    assert result["contract_validation"]["valid"] is True
    assert result["trace_closure"]["trace_closed"] is True


def test_cli_invalid_json_returns_nonzero(tmp_path, capsys):
    path = tmp_path / "invalid.json"
    path.write_text('{"x": NaN}', encoding="utf-8")
    code = main([str(path)])
    assert code == 2
    assert "ERROR:" in capsys.readouterr().err


def test_cli_missing_file_returns_nonzero(tmp_path, capsys):
    code = main([str(tmp_path / "missing.json")])
    assert code == 2
    assert "ERROR:" in capsys.readouterr().err
