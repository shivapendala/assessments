"""
ElevateIQ — Export Service
Generates CSV and XLSX result exports for admin download.
"""
import csv
import io
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, GradientFill
)
from openpyxl.utils import get_column_letter
from flask import make_response

from models.models import Submission, db


# ─────────────────────────────────────────────
# Shared data fetcher
# ─────────────────────────────────────────────

def _get_results(search: str = '', assessment_id: int = None, status: str = None):
    """Fetch all submissions with optional search and status filter."""
    from sqlalchemy.orm import joinedload
    query = (
        db.session.query(Submission)
        .options(
            joinedload(Submission.candidate),
            joinedload(Submission.assessment)
        )
        .filter(Submission.status != 'in_progress')
        .order_by(
            Submission.percentage.desc(),
            Submission.score.desc(),
            Submission.submitted_at.desc()
        )
    )

    if status and status.lower() in ('pass', 'fail'):
        query = query.filter(Submission.status == status.lower())

    if assessment_id:
        query = query.filter(Submission.assessment_id == assessment_id)

    if search:
        from models.models import Candidate
        like = f'%{search}%'
        query = query.join(Submission.candidate).filter(
            db.or_(
                Candidate.full_name.ilike(like),
                Candidate.hall_ticket.ilike(like),
                Candidate.email.ilike(like),
            )
        )

    return query.all()


HEADERS = [
    'Hall Ticket', 'Full Name', 'Email',
    'Assessment', 'Score', 'Total Questions',
    'Percentage (%)', 'Violations', 'Status', 'Submitted At'
]


def _row_data(sub: Submission):
    return [
        sub.candidate.hall_ticket,
        sub.candidate.full_name,
        sub.candidate.email,
        sub.assessment.title,
        sub.score,
        sub.total_questions,
        round(sub.percentage, 2),
        sub.violations,
        sub.status.upper(),
        sub.submitted_at_ist.strftime('%Y-%m-%d %H:%M:%S') if sub.submitted_at_ist else '',
    ]


# ─────────────────────────────────────────────
# CSV Export
# ─────────────────────────────────────────────

def export_csv(search: str = '', assessment_id: int = None, status: str = None):
    """Return a Flask Response with CSV attachment."""
    submissions = _get_results(search, assessment_id, status)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(HEADERS)
    for sub in submissions:
        writer.writerow(_row_data(sub))

    content = output.getvalue()
    output.close()

    status_suffix = f'_{status.lower()}' if status and status.lower() in ('pass', 'fail') else ''
    filename = f'elevateiq_results{status_suffix}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    response = make_response(content)
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return response


# ─────────────────────────────────────────────
# XLSX Export
# ─────────────────────────────────────────────

def export_xlsx(search: str = '', assessment_id: int = None, status: str = None):
    """Return a Flask Response with XLSX attachment."""
    submissions = _get_results(search, assessment_id, status)

    wb = Workbook()
    ws = wb.active
    ws.title = 'Results'

    # ── Styles ──────────────────────────────
    header_fill = PatternFill('solid', fgColor='2D1B69')
    header_font = Font(bold=True, color='FFFFFF', size=11)
    pass_fill = PatternFill('solid', fgColor='D1FAE5')
    fail_fill = PatternFill('solid', fgColor='FEE2E2')
    alt_fill = PatternFill('solid', fgColor='F5F3FF')
    center = Alignment(horizontal='center', vertical='center', wrap_text=True)
    left = Alignment(horizontal='left', vertical='center', wrap_text=True)
    thin = Side(style='thin', color='C4B5FD')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    col_widths = [18, 28, 32, 30, 8, 16, 16, 12, 10, 22]

    # ── Title row ──────────────────────────
    ws.merge_cells('A1:J1')
    title_cell = ws['A1']
    status_title = f' ({status.upper()} ONLY)' if status and status.lower() in ('pass', 'fail') else ''
    title_cell.value = f'ElevateIQ — Assessment Results Export{status_title}  ({datetime.utcnow().strftime("%d %b %Y %H:%M UTC")})'
    title_cell.font = Font(bold=True, color='4C1D95', size=13)
    title_cell.fill = PatternFill('solid', fgColor='EDE9FE')
    title_cell.alignment = center
    ws.row_dimensions[1].height = 26

    # ── Header row ─────────────────────────
    ws.append(HEADERS)
    for col_idx, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=2, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border
    ws.row_dimensions[2].height = 22

    # ── Data rows ──────────────────────────
    for row_idx, sub in enumerate(submissions, start=3):
        row = _row_data(sub)
        ws.append(row)
        status_upper = sub.status.upper()
        row_fill = pass_fill if status_upper == 'PASS' else (
            fail_fill if status_upper == 'FAIL' else None
        )
        for col_idx in range(1, len(HEADERS) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border
            if row_fill:
                cell.fill = row_fill
            elif row_idx % 2 == 0:
                cell.fill = alt_fill
            if col_idx in (1, 5, 6, 7, 8, 9):
                cell.alignment = center
            else:
                cell.alignment = left

    # ── Column widths ──────────────────────
    for i, width in enumerate(col_widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = width

    # ── Freeze header rows ─────────────────
    ws.freeze_panes = 'A3'

    # ── Auto filter ────────────────────────
    if submissions:
        ws.auto_filter.ref = f'A2:J{len(submissions) + 2}'

    # ── Stream response ────────────────────
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    status_suffix = f'_{status.lower()}' if status and status.lower() in ('pass', 'fail') else ''
    filename = f'elevateiq_results{status_suffix}_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.headers['Content-Type'] = (
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    return response
