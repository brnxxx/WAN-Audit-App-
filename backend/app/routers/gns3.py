import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import gns3_service
from app.routers.auth import get_current_admin
from app.models import Admin, InfrastructureLog

router = APIRouter(prefix="/gns3", tags=["gns3"])


class DiagnosticRequest(BaseModel):
    target: str = Field(min_length=3, max_length=45)
    count: int = Field(default=4, ge=1, le=5)
    project_id: str | None = Field(default=None, min_length=1, max_length=100)
    source_node_id: str | None = Field(default=None, min_length=1, max_length=100)


class RouterCommandRequest(BaseModel):
    source_node_id: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=3, max_length=120)


def _record_log(
    db: Session,
    project_id: str,
    event_type: str,
    status: str,
    message: str,
    *,
    source: str | None = None,
    target: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(InfrastructureLog(
        project_id=project_id,
        event_type=event_type,
        status=status,
        source=source,
        target=target,
        message=message,
        details=json.dumps(details, ensure_ascii=True) if details else None,
    ))
    db.commit()


@router.get("/projects/{project_id}/logs")
def infrastructure_logs(
    project_id: str,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    safe_limit = max(1, min(limit, 500))
    return (
        db.query(InfrastructureLog)
        .filter(InfrastructureLog.project_id == project_id)
        .order_by(InfrastructureLog.created_at.desc(), InfrastructureLog.id.desc())
        .limit(safe_limit)
        .all()
    )


def _all_infrastructure_logs(project_id: str, db: Session) -> list[InfrastructureLog]:
    return (
        db.query(InfrastructureLog)
        .filter(InfrastructureLog.project_id == project_id)
        .order_by(InfrastructureLog.created_at.asc(), InfrastructureLog.id.asc())
        .limit(5000)
        .all()
    )


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _pdf_text(value: str, x: int, y: int, size: int = 8, color: tuple[float, float, float] = (0.12, 0.18, 0.25)) -> str:
    red, green, blue = color
    return f"{red} {green} {blue} rg BT /F1 {size} Tf {x} {y} Td ({_pdf_escape(value)}) Tj ET"


def _pdf_rect(x: int, y: int, width: int, height: int, color: tuple[float, float, float]) -> str:
    red, green, blue = color
    return f"{red} {green} {blue} rg {x} {y} {width} {height} re f"


def _build_log_pdf(project_id: str, logs: list[InfrastructureLog]) -> bytes:
    counts = {
        "total": len(logs),
        "ok": sum(log.status == "ok" for log in logs),
        "issue": sum(log.status == "issue" for log in logs),
        "error": sum(log.status == "error" for log in logs),
    }
    rows_per_page = 12
    pages = [logs[index:index + rows_per_page] for index in range(0, len(logs), rows_per_page)] or [[]]
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    ]
    page_objects: list[int] = []
    for index, page_logs in enumerate(pages):
        page_object = 3 + index * 2
        content_object = page_object + 1
        page_objects.append(page_object)
        commands = [
            _pdf_rect(0, 0, 612, 792, (0.97, 0.98, 0.99)),
            _pdf_rect(0, 742, 612, 50, (0.03, 0.08, 0.14)),
            _pdf_text("WAN AUDIT", 36, 766, 15, (0.38, 0.9, 1.0)),
            _pdf_text("INFRASTRUCTURE LOG REPORT", 36, 750, 8, (0.75, 0.84, 0.91)),
            _pdf_text(f"Project: {project_id}", 410, 766, 8, (0.85, 0.9, 0.94)),
            _pdf_text(f"Page {index + 1}/{len(pages)}", 510, 750, 7, (0.65, 0.75, 0.83)),
        ]
        if index == 0:
            cards = [
                ("TOTAL EVENTS", counts["total"], 36, (0.08, 0.32, 0.46)),
                ("HEALTHY", counts["ok"], 174, (0.06, 0.45, 0.3)),
                ("ISSUES", counts["issue"], 312, (0.75, 0.43, 0.04)),
                ("ERRORS", counts["error"], 450, (0.72, 0.12, 0.2)),
            ]
            for label, value, x, color in cards:
                commands.append(_pdf_rect(x, 690, 126, 34, (1, 1, 1)))
                commands.append(_pdf_rect(x, 690, 4, 34, color))
                commands.append(_pdf_text(label, x + 12, 711, 6, (0.35, 0.42, 0.5)))
                commands.append(_pdf_text(str(value), x + 12, 696, 13, color))
            start_y = 660
        else:
            start_y = 700
        commands.extend([
            _pdf_text("TIME", 36, start_y, 7, (0.25, 0.35, 0.45)),
            _pdf_text("EVENT", 150, start_y, 7, (0.25, 0.35, 0.45)),
            _pdf_text("TARGET / SOURCE", 270, start_y, 7, (0.25, 0.35, 0.45)),
            _pdf_text("MESSAGE", 430, start_y, 7, (0.25, 0.35, 0.45)),
        ])
        y = start_y - 18
        for row_index, log in enumerate(page_logs):
            if row_index % 2 == 0:
                commands.append(_pdf_rect(30, y - 10, 552, 28, (0.93, 0.96, 0.98)))
            color = {"ok": (0.06, 0.45, 0.3), "issue": (0.75, 0.43, 0.04), "error": (0.72, 0.12, 0.2)}.get(log.status, (0.25, 0.35, 0.45))
            timestamp = log.created_at.strftime("%Y-%m-%d %H:%M") if log.created_at else "-"
            target_source = f"{log.target or '-'} / {log.source or '-'}"
            commands.extend([
                _pdf_text(timestamp, 36, y, 7, (0.2, 0.28, 0.36)),
                _pdf_text(f"{log.event_type.upper()} · {log.status.upper()}", 150, y, 7, color),
                _pdf_text(target_source[:27], 270, y, 7, (0.2, 0.28, 0.36)),
                _pdf_text(log.message[:29], 430, y, 7, (0.2, 0.28, 0.36)),
            ])
            y -= 36
        commands.append(_pdf_text("Generated by WAN Audit", 36, 24, 7, (0.4, 0.48, 0.56)))
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {3 + len(pages) * 2} 0 R >> >> "
            f"/Contents {content_object} 0 R >>".encode()
        )
        objects.append(
            f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
    objects[1] = (
        f"<< /Type /Pages /Kids [{ ' '.join(f'{item} 0 R' for item in page_objects) }] "
        f"/Count {len(page_objects)} >>".encode()
    )
    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    return bytes(output)


@router.get("/projects/{project_id}/logs.csv")
def export_infrastructure_logs_csv(
    project_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    logs = _all_infrastructure_logs(project_id, db)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(["WAN AUDIT - INFRASTRUCTURE LOG EXPORT"])
    writer.writerow(["Infrastructure", project_id])
    writer.writerow(["Total events", len(logs)])
    writer.writerow(["Healthy", sum(log.status == "ok" for log in logs)])
    writer.writerow(["Issues", sum(log.status == "issue" for log in logs)])
    writer.writerow(["Errors", sum(log.status == "error" for log in logs)])
    writer.writerow([])
    writer.writerow(["Event ID", "Infrastructure", "Event type", "Status", "Source device", "Target", "Message", "Details", "Created at"])
    for log in logs:
        writer.writerow([
            log.id, log.project_id, log.event_type, log.status, log.source or "",
            log.target or "", log.message, log.details or "",
            log.created_at.isoformat(sep=" ") if log.created_at else "",
        ])
    return Response(
        content="\ufeff" + stream.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="infrastructure-{project_id}-logs.csv"'},
    )


@router.get("/projects/{project_id}/logs.pdf")
def export_infrastructure_logs_pdf(
    project_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    pdf = _build_log_pdf(project_id, _all_infrastructure_logs(project_id, db))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="infrastructure-{project_id}-logs.pdf"'},
    )


@router.get("/projects")
def list_projects(current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_projects()
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}/nodes")
def list_nodes(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project_nodes(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}/links")
def list_links(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project_links(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/projects/{project_id}")
def get_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.get_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/start")
def start_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.start_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/stop")
def stop_project(project_id: str, current_admin: Admin = Depends(get_current_admin)):
    try:
        return gns3_service.stop_project(project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/projects/{project_id}/nodes/{node_id}/{action}")
def control_node(project_id: str, node_id: str, action: str, current_admin: Admin = Depends(get_current_admin)):
    actions = {
        "start": gns3_service.start_node,
        "stop": gns3_service.stop_node,
        "reload": gns3_service.reload_node,
    }
    if action not in actions:
        raise HTTPException(status_code=400, detail="Action nœud invalide")
    try:
        return actions[action](project_id, node_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.get("/commands")
def command_guide(current_admin: Admin = Depends(get_current_admin)):
    return gns3_service.COMMAND_GUIDE


@router.post("/projects/{project_id}/nodes/command")
def execute_router_command(
    project_id: str,
    payload: RouterCommandRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    try:
        result = gns3_service.execute_router_command(
            project_id, payload.source_node_id, payload.command
        )
        _record_log(
            db,
            project_id,
            "command",
            "ok",
            f"Commande exécutée : {result['command']}",
            source=result["source"],
            details=result,
        )
        return result
    except gns3_service.GNS3ServiceError as exc:
        _record_log(
            db,
            project_id,
            "error",
            "error",
            str(exc),
            source=payload.source_node_id,
            details={"command": payload.command},
        )
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/diagnostics/ping")
def diagnostic_ping(
    payload: DiagnosticRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if not payload.project_id:
        raise HTTPException(status_code=400, detail="Un projet GNS3 est requis pour journaliser cette infrastructure")
    try:
        result = gns3_service.ping_host(
            payload.target.strip(), payload.count, payload.project_id, payload.source_node_id
        )
        _record_log(
            db, payload.project_id, "ping", "ok" if result["reachable"] else "issue",
            "Ping joignable" if result["reachable"] else "Ping injoignable",
            source=result.get("source"), target=result["target"], details=result,
        )
        return result
    except gns3_service.GNS3ServiceError as exc:
        _record_log(db, payload.project_id, "error", "error", str(exc), target=payload.target.strip())
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/diagnostics/traceroute")
def diagnostic_traceroute(
    payload: DiagnosticRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    if not payload.project_id:
        raise HTTPException(status_code=400, detail="Un projet GNS3 est requis pour journaliser cette infrastructure")
    try:
        result = gns3_service.traceroute_host(
            payload.target.strip(), payload.project_id, payload.source_node_id
        )
        _record_log(
            db, payload.project_id, "traceroute", "ok" if result["reachable"] else "issue",
            "Traceroute terminé" if result["reachable"] else "Traceroute incomplet",
            source=result.get("source"), target=result["target"], details=result,
        )
        return result
    except gns3_service.GNS3ServiceError as exc:
        _record_log(db, payload.project_id, "error", "error", str(exc), target=payload.target.strip())
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/projects/{project_id}/import")
def import_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    try:
        return gns3_service.import_project_topology(db, project_id)
    except gns3_service.GNS3ServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))