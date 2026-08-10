#!/usr/bin/env python3
"""Export logs/response_times.csv (auto-logged by server.py every turn) into an
Excel report matching the component-summary + Question/Answer layout.

    python export_response_report.py                 # uses all logged turns
    python export_response_report.py --last 3         # only the last N turns
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

from src.config import CONFIG

ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "response_times.csv"
OUT_PATH = ROOT / "response_time_report.xlsx"

INK, HEADER, BAND, WHITE, GREY = "0F2E2A", "0E7C6B", "EAF4F1", "FFFFFF", "6A7E7A"
GOOD, MID, BAD = "C9E9D2", "FCEFC7", "F6C9C4"


def fill(c):
    return PatternFill("solid", fgColor=c)


thin = Side(style="thin", color="D3E0DC")
border = Border(left=thin, right=thin, top=thin, bottom=thin)


def perf_fill(seconds: float) -> str:
    if seconds <= 1.0:
        return GOOD
    if seconds <= 3.0:
        return MID
    return BAD


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=None, help="only include the last N logged turns")
    args = ap.parse_args()

    if not LOG_PATH.exists():
        raise SystemExit(f"No log file at {LOG_PATH} yet — run the server and test via mic first.")

    with open(LOG_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if args.last:
        rows = rows[-args.last:]
    if not rows:
        raise SystemExit("Log file is empty — nothing to export.")

    wb = Workbook()
    ws = wb.active
    ws.title = "Response Time Report"
    ws.sheet_view.showGridLines = False

    ws.merge_cells("A1:D1")
    t = ws["A1"]
    t.value = "Voice Agent — Response Time Report"
    t.font = Font(size=18, bold=True, color=INK)
    ws.row_dimensions[1].height = 30

    ws.merge_cells("A2:D2")
    s = ws["A2"]
    s.value = f"{len(rows)} sample(s) — live mic test, {rows[0]['timestamp']} to {rows[-1]['timestamp']}"
    s.font = Font(size=9, italic=True, color=GREY)

    # ---- Component summary table (Model / Configuration / Performance) ------
    r = 4
    headers = ["", "Speech to Text", "LLM", "Text to Speech"]
    for i, h in enumerate(headers, 1):
        c = ws.cell(r, i, h)
        c.font = Font(bold=True, color=WHITE, size=10)
        c.fill = fill(HEADER)
        c.alignment = Alignment("center", "center")
        c.border = border
    r += 1

    avg_stt = sum(float(x["stt_s"]) for x in rows) / len(rows)
    avg_llm = sum(float(x["llm_s"]) for x in rows) / len(rows)
    tts_vals = [float(x["tts_s"]) for x in rows if x["tts_s"]]
    avg_tts = sum(tts_vals) / len(tts_vals) if tts_vals else None

    cpu_cfg = f"CPU int8, {CONFIG.whisper_cpu_threads} threads, beam={CONFIG.whisper_beam_size}"
    tts_cfg = "CPU, torch" if CONFIG.tts_provider == "silero" else ("CPU, ONNX" if CONFIG.tts_provider == "piper" else "Online API")
    llm_cfg = "Local, Ollama HTTP" if CONFIG.llm_provider == "ollama" else "Cloud API"

    table = [
        ("Model", rows[0]["stt_model"], rows[0]["llm_model"], rows[0]["tts_provider"]),
        ("Configuration", cpu_cfg, llm_cfg, tts_cfg),
        ("Avg. Performance", f"{avg_stt:.2f}s", f"{avg_llm:.2f}s",
         f"{avg_tts:.2f}s" if avg_tts is not None else "n/a"),
    ]
    perf_vals = [avg_stt, avg_llm, avg_tts]
    for label, *vals in table:
        ws.cell(r, 1, label).font = Font(bold=True, size=10, color=INK)
        ws.cell(r, 1).border = border
        ws.cell(r, 1).fill = fill(BAND)
        for i, v in enumerate(vals, 2):
            c = ws.cell(r, i, v)
            c.border = border
            c.alignment = Alignment("center", "center")
            c.font = Font(size=10, color=INK)
            if label == "Avg. Performance" and perf_vals[i - 2] is not None:
                c.fill = fill(perf_fill(perf_vals[i - 2]))
                c.font = Font(size=10, bold=True, color=INK)
        r += 1

    avg_total = sum(float(x["total_s"]) for x in rows) / len(rows)
    ws.cell(r, 1, "Avg. Total round trip").font = Font(bold=True, size=10, color=INK)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    tc = ws.cell(r, 2, f"{avg_total:.2f}s  (STT + LLM + TTS processing time only)")
    tc.font = Font(bold=True, size=11, color=HEADER)
    tc.alignment = Alignment("center", "center")
    r += 2

    # ---- Question / Answer log -----------------------------------------------
    qh = r
    for i, h in enumerate(["#", "Question", "Answer", "STT (s)", "LLM (s)", "TTS (s)", "Total (s)"], 1):
        c = ws.cell(qh, i, h)
        c.font = Font(bold=True, color=WHITE, size=10)
        c.fill = fill(HEADER)
        c.alignment = Alignment("center", "center", wrap_text=True)
        c.border = border
    r += 1
    for idx, row in enumerate(rows, 1):
        vals = [f"Sample {idx}", row["question"], row["answer"],
                row["stt_s"], row["llm_s"], row["tts_s"] or "n/a", row["total_s"]]
        bg = WHITE if idx % 2 else BAND
        for i, v in enumerate(vals, 1):
            c = ws.cell(r, i, v)
            c.border = border
            c.fill = fill(bg)
            c.font = Font(size=10, color=INK)
            c.alignment = Alignment("left" if i in (2, 3) else "center", "center", wrap_text=(i in (2, 3)))
        ws.cell(r, 7).fill = fill(perf_fill(float(row["total_s"])))
        r += 1

    widths = [10, 32, 40, 9, 9, 9, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = f"A{qh + 1}"

    # ---- Sheet 2: By STT model (compare Whisper family variants tested) -----
    by_model: dict[str, list[dict]] = {}
    for row in rows:
        by_model.setdefault(row["stt_model"], []).append(row)

    if len(by_model) > 1:
        ms = wb.create_sheet("By STT Model")
        ms.sheet_view.showGridLines = False
        ms.merge_cells("A1:F1")
        h = ms["A1"]
        h.value = "Whisper Family Comparison — same 3 sentences, full pipeline"
        h.font = Font(size=16, bold=True, color=INK)
        ms.row_dimensions[1].height = 28

        mh = 3
        for i, hd in enumerate(["STT Model", "Samples", "Avg STT (s)", "Avg LLM (s)", "Avg TTS (s)", "Avg Total (s)"], 1):
            c = ms.cell(mh, i, hd)
            c.font = Font(bold=True, color=WHITE, size=10)
            c.fill = fill(HEADER)
            c.alignment = Alignment("center", "center", wrap_text=True)
            c.border = border

        summary = []
        for model, grp in by_model.items():
            n = len(grp)
            a_stt = sum(float(x["stt_s"]) for x in grp) / n
            a_llm = sum(float(x["llm_s"]) for x in grp) / n
            tts_g = [float(x["tts_s"]) for x in grp if x["tts_s"]]
            a_tts = sum(tts_g) / len(tts_g) if tts_g else None
            a_tot = sum(float(x["total_s"]) for x in grp) / n
            summary.append((model, n, a_stt, a_llm, a_tts, a_tot))
        summary.sort(key=lambda x: x[2])  # fastest STT first

        r2 = mh + 1
        for idx, (model, n, a_stt, a_llm, a_tts, a_tot) in enumerate(summary):
            bg = WHITE if idx % 2 else BAND
            vals = [model, n, round(a_stt, 2), round(a_llm, 2),
                     round(a_tts, 2) if a_tts is not None else "n/a", round(a_tot, 2)]
            for i, v in enumerate(vals, 1):
                c = ms.cell(r2, i, v)
                c.border = border
                c.fill = fill(bg)
                c.font = Font(size=10, color=INK, bold=(i == 1))
                c.alignment = Alignment("left" if i == 1 else "center", "center")
            ms.cell(r2, 3).fill = fill(perf_fill(a_stt))
            ms.cell(r2, 6).fill = fill(perf_fill(a_tot))
            ms.cell(r2, 6).font = Font(size=10, bold=True, color=INK)
            r2 += 1
        data_last = r2 - 1

        for i, w in enumerate([26, 10, 12, 12, 12, 13], 1):
            ms.column_dimensions[get_column_letter(i)].width = w

        bc = BarChart()
        bc.type = "col"
        bc.title = "Avg total response time by STT model"
        bc.y_axis.title = "Seconds"
        bc.height = 10
        bc.width = 18
        bc.style = 10
        data_ref = Reference(ms, min_col=6, min_row=mh, max_row=data_last)
        cats_ref = Reference(ms, min_col=1, min_row=mh + 1, max_row=data_last)
        bc.add_data(data_ref, titles_from_data=True)
        bc.set_categories(cats_ref)
        bc.series[0].graphicalProperties.solidFill = "0E7C6B"
        ms.add_chart(bc, f"A{data_last + 3}")

    wb.save(OUT_PATH)
    print(f"Exported {len(rows)} turn(s) -> {OUT_PATH}")
    print(f"Averages: STT={avg_stt:.2f}s  LLM={avg_llm:.2f}s  "
          f"TTS={f'{avg_tts:.2f}s' if avg_tts is not None else 'n/a'}  TOTAL={avg_total:.2f}s")
    if len(by_model) > 1:
        print(f"Also wrote a 'By STT Model' comparison sheet for {len(by_model)} model(s) tested.")


if __name__ == "__main__":
    main()
