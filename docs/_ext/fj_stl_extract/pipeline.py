"""End-to-end extraction over a flip-jump STL checkout.

Reads `conf.json` for the canonical file order, parses each `.fj` file,
attaches doc comments, and builds the cross-file dependency graph.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .dep_graph import DepGraph, build_dep_graph, macro_key
from .doc_attach import DocInfo, attach_docs
from .parser import ConstantNode, FileNode, MacroNode, parse

__all__ = ["StlIndex", "ExtractedFile", "extract_stl", "to_json_dict"]


@dataclass
class ExtractedFile:
    rel_path: str           # "bit/math" — no extension, matches conf.json
    abs_path: str
    source: str
    file_node: FileNode
    docs: dict[int, DocInfo] = field(default_factory=dict)


@dataclass
class StlIndex:
    files: list[ExtractedFile] = field(default_factory=list)
    dep_graph: DepGraph | None = None

    @property
    def all_macros(self) -> list[MacroNode]:
        return [m for f in self.files for m in f.file_node.macros]

    @property
    def all_constants(self) -> list[ConstantNode]:
        return [c for f in self.files for c in f.file_node.constants]


def extract_stl(stl_root: str | Path) -> StlIndex:
    """Extract everything under `stl_root` driven by `conf.json`.

    Raises FileNotFoundError if `conf.json` is missing — meaning the
    flip-jump submodule was never initialised. The Sphinx extension in
    M4 will surface this with a friendly "run `git submodule update`"
    error message.
    """
    root = Path(stl_root).resolve()
    conf_path = root / "conf.json"
    if not conf_path.is_file():
        raise FileNotFoundError(
            f"Missing {conf_path}. The flip-jump submodule does not appear "
            f"to be initialised. Run `git submodule update --init --recursive`."
        )

    conf = json.loads(conf_path.read_text(encoding="utf-8"))
    file_order: list[str] = conf.get("all", [])

    index = StlIndex()
    for rel in file_order:
        abs_path = root / (rel + ".fj")
        if not abs_path.is_file():
            # Skip silently — the file might be added in a future upstream
            # commit but listed in conf.json early. Better to under-document
            # than to crash the build.
            continue
        source = abs_path.read_text(encoding="utf-8")
        file_node = parse(source)
        docs = attach_docs(source, file_node)
        index.files.append(ExtractedFile(
            rel_path=rel,
            abs_path=str(abs_path),
            source=source,
            file_node=file_node,
            docs=docs,
        ))

    index.dep_graph = build_dep_graph(index.all_macros)
    return index


def to_json_dict(index: StlIndex) -> dict[str, Any]:
    """Serialise the index to a plain dict suitable for `json.dumps`."""
    files_out: list[dict[str, Any]] = []
    for f in index.files:
        macros_out: list[dict[str, Any]] = []
        for m in f.file_node.macros:
            doc = f.docs.get(id(m))
            macros_out.append({
                "key": macro_key(m),
                "name": m.name,
                "namespace": ".".join(m.namespace_path),
                "fq_name": m.fq_name,
                "arity": m.arity,
                "params": m.params,
                "locals": m.locals_,
                "requires_labels": m.requires_labels,
                "exports_labels": m.exports_labels,
                "start_line": m.start_line,
                "end_line": m.end_line,
                "doc": _doc_dict(doc),
                "depends_on": sorted(
                    (index.dep_graph.depends_on.get(macro_key(m), set()) if index.dep_graph else set())
                ),
                "used_by": sorted(
                    (index.dep_graph.used_by.get(macro_key(m), set()) if index.dep_graph else set())
                ),
            })
        constants_out = [
            {
                "name": c.name,
                "namespace": ".".join(c.namespace_path),
                "fq_name": c.fq_name,
                "expr": " ".join(t.text for t in c.expr_tokens),
                "start_line": c.start_line,
                "doc": _doc_dict(f.docs.get(id(c))),
            }
            for c in f.file_node.constants
        ]
        files_out.append({
            "rel_path": f.rel_path,
            # `abs_path` deliberately omitted — leaks local filesystem
            # paths if the JSON is ever published. `rel_path` plus the
            # caller-known STL root is enough to locate the source.
            "macros": macros_out,
            "constants": constants_out,
        })
    return {"files": files_out}


def _doc_dict(doc: DocInfo | None) -> dict[str, Any]:
    if doc is None:
        return {}
    return {
        "description": doc.description,
        "time_complexity": doc.time_complexity,
        "space_complexity": doc.space_complexity,
        "requires": doc.requires,
        "output_params": doc.output_params,
    }
