from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from lib.dvpl_converter.classes import CompressionTypes
from lib.dvpl_converter.converter import Converter

ProgressCallback = Callable[[int, int, str], None]


@dataclass
class BatchResult:
    ok: int = 0
    failed: int = 0
    skipped: int = 0


def _output_path(
    path: Path,
    out_name: str,
    output_dir: Path | None,
    root_folder: Path | None = None,
) -> Path:
    if output_dir is None:
        return path.parent / out_name

    if root_folder is not None:
        try:
            relative_parent = path.parent.relative_to(root_folder)
            if str(relative_parent) == ".":
                return output_dir / out_name
            return output_dir / relative_parent / out_name
        except ValueError:
            pass

    return output_dir / out_name


def _display_name(path: Path, root_folder: Path | None) -> str:
    if root_folder is not None:
        try:
            return str(path.relative_to(root_folder))
        except ValueError:
            pass
    return path.name


def _collect_pack_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() != ".dvpl"
    )


def _collect_unpack_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.rglob("*")
        if path.is_file() and path.suffix.lower() == ".dvpl"
    )


def _report_progress(
    on_progress: ProgressCallback | None,
    current: int,
    total: int,
    name: str,
) -> None:
    if on_progress is not None:
        on_progress(current, total, name)


def pack_files(
    paths: list[Path],
    *,
    compression_type: CompressionTypes = CompressionTypes.NONE,
    keep_original: bool = True,
    skip_if_exist: bool = False,
    output_dir: Path | None = None,
    root_folder: Path | None = None,
    on_result: Callable[[str], None] | None = None,
    on_progress: ProgressCallback | None = None,
) -> BatchResult:
    result = BatchResult()
    total = len(paths)
    _report_progress(on_progress, 0, total, "")

    for index, path in enumerate(paths, start=1):
        label = _display_name(path, root_folder)
        _report_progress(on_progress, index - 1, total, label)
        try:
            if path.suffix.lower() == ".dvpl":
                raise ValueError("already a DVPL file")

            out_name = f"{path.name}.dvpl"
            out_path = _output_path(path, out_name, output_dir, root_folder)
            if skip_if_exist and out_path.exists():
                result.skipped += 1
                if on_result:
                    on_result(f"skipped:{label}:{out_path}")
                continue

            Converter.pack_file(
                path,
                out_name,
                out_path.parent,
                keep_original,
                compression_type,
            )
            result.ok += 1
            if on_result:
                on_result(f"packed:{label}:{out_path}")
        except Exception as exc:
            result.failed += 1
            if on_result:
                on_result(f"failed:{label}:{exc}")
        finally:
            _report_progress(on_progress, index, total, label)

    return result


def unpack_files(
    paths: list[Path],
    *,
    keep_original: bool = True,
    skip_if_exist: bool = False,
    output_dir: Path | None = None,
    root_folder: Path | None = None,
    on_result: Callable[[str], None] | None = None,
    on_progress: ProgressCallback | None = None,
) -> BatchResult:
    result = BatchResult()
    total = len(paths)
    _report_progress(on_progress, 0, total, "")

    for index, path in enumerate(paths, start=1):
        label = _display_name(path, root_folder)
        _report_progress(on_progress, index - 1, total, label)
        try:
            if path.suffix.lower() != ".dvpl":
                raise ValueError("not a DVPL file")

            out_name = path.stem
            out_path = _output_path(path, out_name, output_dir, root_folder)
            if skip_if_exist and out_path.exists():
                result.skipped += 1
                if on_result:
                    on_result(f"skipped:{label}:{out_path}")
                continue

            Converter.unpack_file(path, out_name, out_path.parent, keep_original)
            result.ok += 1
            if on_result:
                on_result(f"unpacked:{label}:{out_path}")
        except Exception as exc:
            result.failed += 1
            if on_result:
                on_result(f"failed:{label}:{exc}")
        finally:
            _report_progress(on_progress, index, total, label)

    return result


def pack_folder(
    folder: Path,
    *,
    compression_type: CompressionTypes = CompressionTypes.NONE,
    keep_original: bool = True,
    skip_if_exist: bool = False,
    output_dir: Path | None = None,
    on_result: Callable[[str], None] | None = None,
    on_progress: ProgressCallback | None = None,
) -> BatchResult:
    files = _collect_pack_files(folder)
    return pack_files(
        files,
        compression_type=compression_type,
        keep_original=keep_original,
        skip_if_exist=skip_if_exist,
        output_dir=output_dir,
        root_folder=folder,
        on_result=on_result,
        on_progress=on_progress,
    )


def unpack_folder(
    folder: Path,
    *,
    keep_original: bool = True,
    skip_if_exist: bool = False,
    output_dir: Path | None = None,
    on_result: Callable[[str], None] | None = None,
    on_progress: ProgressCallback | None = None,
) -> BatchResult:
    files = _collect_unpack_files(folder)
    return unpack_files(
        files,
        keep_original=keep_original,
        skip_if_exist=skip_if_exist,
        output_dir=output_dir,
        root_folder=folder,
        on_result=on_result,
        on_progress=on_progress,
    )
