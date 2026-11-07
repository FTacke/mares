"""network_v0 standard figures: the shared figure functions of network_v1 with the v0 scheme (synthetic packages only)."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

import network_v0_fixtures as fx
from mares.core.refs import StorageRef
from mares.core.roots import Roots, load_root_specs
from mares.network_v0 import standard
from mares.network_v0.build import build_network
from mares.network_v0.cli import main as v0_main
from mares.network_v0.package import read_package
from mares.network_v0.run import PipelineError, render_case
from mares.network_v0.figures.style import rc
from mares.network_v1.figures import base
from mares.network_v1.figures.networks import g1_layout

SPECS = load_root_specs()


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    return read_package(fx.standard_package(tmp_path_factory.mktemp("pkg") / "contents", n=22))


@pytest.fixture(scope="module")
def ctx(dataset):
    return standard.figure_context(dataset, build_network(dataset), case_code="0000")


def texts(figure) -> list[str]:
    return [t.get_text() for t in figure.findobj(lambda a: hasattr(a, "get_text") and a.get_text())]


def test_every_contact_is_in_the_figure_case_with_its_v0_codes(dataset, ctx):
    assert ctx.case.contact_ids == [c.contact_id for c in dataset.contacts] and len(ctx.case.contacts) == 22  # A16-A22: second sheet
    for c, v in zip(dataset.contacts, ctx.case.contacts):
        assert v.closeness.values == c.codes["closeness"].codes  # the v0 table value, never recoded
        assert v.relation_type.values == c.codes["relation"].codes  # several relation codes stay several
        assert v.contact_frequency.values == c.codes["contact_frequency"].codes
        assert ctx.case.communication[c.contact_id].forms.values == c.codes["media"].codes


def test_only_confirmed_groups_and_ties(dataset, ctx):
    network = build_network(dataset)
    assert {tuple(sorted((t.a, t.b))) for t in network.ties if t.state.value == "yes"} == set(ctx.derived.confirmed_edges)
    confirmed = {g.group_id for g in dataset.groups if g.assessment == "confirmed"}
    assert {g.id for g in ctx.case.groups} <= confirmed


def test_the_scheme_uses_the_v0_scales_and_labels(ctx):
    scheme = ctx.scheme
    assert scheme.version == "network_v0" and not scheme.belonging
    assert [r[0] for r in scheme.closeness_rows(False)] == [5.0, 4.0, 3.0, 2.0, 1.0]  # 5 = very close on top
    assert scheme.closeness_rows(False)[0][1] == "5 · sehr nah"
    assert [r[0] for r in scheme.frequency_rows()] == ["5", "4", "3", "2", "1"]  # daily on top
    assert scheme.function_keys == tuple(fx.CODEBOOK["function"])
    assert scheme.area_labels[base.Area.MITTELHESSEN] == "Region Marburg"


def test_g1_rings_are_the_table_value_not_a_map_position(ctx):
    positions = g1_layout(ctx)
    for c in ctx.case.contacts:
        value = ctx.scheme.closeness(c)
        if value is not None:
            assert math.hypot(*positions[c.id]) == pytest.approx(6 - value)  # 5 innermost ... 1 outermost
    with rc():
        shown = texts(standard.V1_FIGURES[0].draw(ctx))
    assert "Tabellenwert der Erhebung,\nnicht die Kartenposition" in shown


def test_several_relation_codes_give_a_split_node_and_no_main_relation(ctx):
    several = [c.id for c in ctx.case.contacts if len(c.relation_type.values) > 1]
    assert several
    fill = ctx.scheme.fill(ctx.case, several[0])
    assert isinstance(fill, tuple) and len(fill) == len(ctx.case.contact(several[0]).relation_type.values)
    title, entries = ctx.scheme.relation_section(ctx.case)
    assert title == "Beziehung" and any(kind == "split" for kind, _l, _p in entries)


def test_the_figures_name_the_version(ctx, tmp_path):
    entries = standard.render_standard(ctx, tmp_path, ("png",))
    assert [e["code"] for e in entries] == list(standard.STANDARD_CODES)
    assert next(e for e in entries if e["code"] == "X1")["status"] == "skipped"  # no map sources given: never drawn from elsewhere
    with rc():
        shown = texts(standard.V1_FIGURES[1].draw(ctx))
    assert "MARES · network_v0 · 22 Kontakte" in shown and "FALL · v0-Pilot 0000-1" in shown


def test_a_codebook_with_another_meaning_is_refused(tmp_path):
    book = {**fx.CODEBOOK, "relation": {**fx.CODEBOOK["relation"], "5": "Nachbarschaft"}}
    data = read_package(fx.build_package(tmp_path / "p", codebook=book))
    with pytest.raises(standard.SchemeError):
        standard.figure_context(data, build_network(data), case_code="0000")


# ------------------------------------------------------------------------------------ registered case ---
def _machine(tmp_path: Path) -> tuple[Roots, Path]:
    folders = {name: tmp_path / name for name in ("checkout", "workspace", "intake")}
    for f in folders.values():
        f.mkdir()
    (folders["workspace"] / "runs").mkdir()
    pkg = fx.standard_package(folders["intake"] / "inbox" / "delivery" / "contents", n=22)
    case = folders["intake"] / "network_v0" / "pilots" / "0000" / "data"
    case.mkdir(parents=True)
    pointer = {"format": "mares-network-v0-case-pointer/v1", "dataset_version": "network_v0", "case_code": "0000", "source_label": fx.LABEL,
               "case_type": "pilot", "empirical_analysis_eligible": False,
               "package": {"ref": {"root": "INTAKE", "rel": "inbox/delivery/contents"},
                           "files": [{"name": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(pkg.iterdir())]}}
    (case / "case.json").write_text(json.dumps(pointer), encoding="utf-8")
    env = {"MARES_WORKSPACE_ROOT": str(folders["workspace"]), "MARES_INTAKE_ROOT": str(folders["intake"])}
    return Roots(SPECS, env, checkout=folders["checkout"]), folders["intake"]


def test_render_case_writes_the_standard_figures_into_graphics_and_leaves_the_pointer(tmp_path):
    roots, intake = _machine(tmp_path)
    pointer = (intake / "network_v0/pilots/0000/data/case.json").read_bytes()
    result = render_case(roots, StorageRef("INTAKE", "network_v0/pilots/0000"))
    assert result.status == "COMPLETED"
    graphics = intake / "network_v0/pilots/0000/graphics"
    names = {p.name for p in graphics.iterdir()}
    assert names == {f for f in standard.expected_files("0000", ("png", "svg")) if "_X1_" not in f}  # X1: no map sources here
    assert (intake / "network_v0/pilots/0000/data/case.json").read_bytes() == pointer  # pilot status and eligibility untouched


def test_render_case_refuses_a_changed_package(tmp_path):
    roots, intake = _machine(tmp_path)
    with open(intake / "inbox/delivery/contents/contacts.csv", "a", encoding="utf-8") as f:
        f.write("\n")
    with pytest.raises(PipelineError):
        render_case(roots, StorageRef("INTAKE", "network_v0/pilots/0000"))
    assert v0_main(["render-case", "--case", "INTAKE:network_v0/pilots/0000"], roots=roots) == 1


def test_categories_without_any_contact_are_not_drawn_but_scale_steps_are(ctx):
    with rc():
        p5 = texts(next(s for s in standard.V1_FIGURES if s.code == "P5").draw(ctx))
        p4 = texts(next(s for s in standard.V1_FIGURES if s.code == "P4").draw(ctx))
    assert not any(t.endswith("n = 0") for t in p5)  # no empty function column
    assert all(f"{v} · " in " ".join(p5) for v in range(5, 0, -1))  # all five closeness steps stay
    used = {code for b in ctx.case.communication.values() for code in b.languages.values}
    shown = {code for code, label in ctx.scheme.language_rows(ctx.case)[0] if label in p4}
    assert shown == used
