from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import joblib


BASE_DIR = Path(__file__).resolve().parents[1]  # .../artifacts/modeling_results
ARTIFACTS_DIR = Path(__file__).resolve().parents[2]  # .../artifacts
OUT_DIR = Path(__file__).resolve().parent


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    return str(value)


def discover_pickles_by_group() -> dict[str, list[Path]]:
    groups = {
        "trained_models": BASE_DIR / "trained_models",
        "pipeline_artifact": ARTIFACTS_DIR / "pipeline_artifact",
    }
    discovered: dict[str, list[Path]] = {}
    for name, folder in groups.items():
        if folder.exists():
            discovered[name] = sorted(folder.glob("*.pkl"))
        else:
            discovered[name] = []
    return discovered


def summarize_model(path: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_path": str(path),
        "artifact_name": path.name,
    }

    try:
        model, stubbed_classes = load_with_stubbed_main_classes(path)
        if stubbed_classes:
            record["stubbed_main_classes"] = stubbed_classes
    except Exception as exc:
        record["load_status"] = "failed"
        record["error"] = str(exc)
        return record

    record["load_status"] = "ok"
    record["object_type"] = type(model).__name__
    record["module"] = type(model).__module__
    record["model_repr"] = str(model)

    if hasattr(model, "steps"):  # sklearn Pipeline
        steps = getattr(model, "steps", [])
        record["pipeline_steps"] = [step_name for step_name, _ in steps]
        if steps:
            record["final_estimator_type"] = type(steps[-1][1]).__name__

    if hasattr(model, "classes_"):
        record["classes_"] = _json_safe(getattr(model, "classes_"))
    if hasattr(model, "n_features_in_"):
        record["n_features_in_"] = int(getattr(model, "n_features_in_"))

    if hasattr(model, "get_params"):
        params = model.get_params(deep=False)
        record["params"] = _json_safe(params)

    # Quick attribute snapshot for engineering inspection
    attrs = [a for a in dir(model) if not a.startswith("__")]
    important = [
        "steps",
        "named_steps",
        "predict",
        "predict_proba",
        "transform",
        "fit",
        "get_params",
        "classes_",
        "n_features_in_",
    ]
    underscore_attrs = [a for a in attrs if a.endswith("_")]
    record["important_attributes"] = [a for a in important if a in attrs]
    record["learned_attributes_sample"] = sorted(underscore_attrs)[:80]

    # Optional training artifacts often useful to engineers
    if hasattr(model, "best_iteration_"):
        record["best_iteration_"] = _json_safe(getattr(model, "best_iteration_"))
    if hasattr(model, "n_iter_"):
        record["n_iter_"] = _json_safe(getattr(model, "n_iter_"))
    if hasattr(model, "loss_"):
        record["loss_"] = _json_safe(getattr(model, "loss_"))
    if hasattr(model, "best_loss_"):
        record["best_loss_"] = _json_safe(getattr(model, "best_loss_"))

    return record


def load_with_stubbed_main_classes(path: Path, max_retry: int = 8) -> tuple[Any, list[str]]:
    """
    Handle joblib artifacts that reference classes serialized from __main__
    (common when training/exporting inside notebooks).
    """
    import __main__

    stubbed: list[str] = []
    pattern = re.compile(r"Can't get attribute '([^']+)' on <module '__main__'")

    for _ in range(max_retry):
        try:
            model = joblib.load(path)
            return model, stubbed
        except Exception as exc:
            msg = str(exc)
            match = pattern.search(msg)
            if not match:
                raise

            missing_cls = match.group(1)
            if hasattr(__main__, missing_cls):
                raise

            # Minimal placeholder class so unpickling can proceed.
            stub_cls = type(
                missing_cls,
                (),
                {
                    "__init__": lambda self, *args, **kwargs: self.__dict__.update(kwargs),
                    "fit": lambda self, X=None, y=None: self,
                    "transform": lambda self, X: X,
                },
            )
            setattr(__main__, missing_cls, stub_cls)
            stubbed.append(missing_cls)

    raise RuntimeError(f"Failed to load {path} after stubbing: {stubbed}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pkl_by_group = discover_pickles_by_group()
    all_paths = [path for paths in pkl_by_group.values() for path in paths]
    model_records = [summarize_model(path) for path in all_paths]
    pipeline_paths = pkl_by_group["pipeline_artifact"]
    pipeline_records = [summarize_model(path) for path in pipeline_paths]

    # Persist reports to avoid rerunning inspection repeatedly.
    artifact_json = OUT_DIR / "model_comparison_artifact_report.json"
    pipeline_json = OUT_DIR / "pipeline_artifact_report.json"
    # artifact_csv = OUT_DIR / "model_artifact_report.csv"

    payload = {
        "base_dir": str(BASE_DIR),
        "num_pickles_found": len(all_paths),
        "counts_by_group": {k: len(v) for k, v in pkl_by_group.items()},
        "pickles": [_json_safe(r) for r in model_records],
        "data_source": "pkl_only",
    }
    artifact_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    pipeline_payload = {
        "base_dir": str(BASE_DIR),
        "artifacts_dir": str(ARTIFACTS_DIR),
        "pipeline_groups": ["pipeline_artifact"],
        "num_pipeline_pickles_found": len(pipeline_paths),
        "pickles": [_json_safe(r) for r in pipeline_records],
        "data_source": "pkl_only",
    }
    pipeline_json.write_text(json.dumps(pipeline_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Avoid pandas dependency; write simple csv for portability.
    if model_records:
        all_keys = sorted({key for row in model_records for key in row.keys()})
        lines = [",".join(all_keys)]
        for row in model_records:
            values = []
            for key in all_keys:
                value = _json_safe(row.get(key, ""))
                text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                text = text.replace('"', '""')
                values.append(f'"{text}"')
            lines.append(",".join(values))
        # artifact_csv.write_text("\n".join(lines), encoding="utf-8-sig")
    # else:
        # artifact_csv.write_text("artifact_path,load_status\n", encoding="utf-8-sig")

    print(f"[OK] Wrote artifact report: {artifact_json}")
    print(f"[OK] Wrote pipeline report: {pipeline_json}")
    print(f"[INFO] Counts by group: { {k: len(v) for k, v in pkl_by_group.items()} }")
    # print(f"[OK] Wrote artifact table:  {artifact_csv}")
    print("[INFO] Metrics CSV files are intentionally ignored (pkl-only mode).")


if __name__ == "__main__":
    main()