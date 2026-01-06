import io
import os
import zipfile
import uuid
import asyncio
from typing import List, Dict
from docx import Document
from docxcompose.composer import Composer
from docx.shared import Pt
from docx.enum.section import WD_ORIENT, WD_SECTION
from pypdf import PdfReader
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from adobe.pdfservices.operation.auth.service_principal_credentials import (
    ServicePrincipalCredentials,
)
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import (
    ExportPDFParams,
)
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import (
    ExportPDFTargetFormat,
)
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import (
    ExportPDFResult,
)
from fastapi import Query

# --------------------------------------------------
# App + CORS
# --------------------------------------------------
app = FastAPI(title="Batch PDF → DOCX Converter")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

# --------------------------------------------------
# Adobe credentials
# --------------------------------------------------
ADOBE_CLIENT_ID = os.getenv("PDF_SERVICES_CLIENT_ID")
ADOBE_CLIENT_SECRET = os.getenv("PDF_SERVICES_CLIENT_SECRET")

if not ADOBE_CLIENT_ID or not ADOBE_CLIENT_SECRET:
    raise RuntimeError("Adobe credentials not set")

# --------------------------------------------------
# Global job store
# --------------------------------------------------
JOB_STATUS: Dict[str, Dict[str, Dict]] = {}
JOB_ZIPS: Dict[str, bytes] = {}

# --------------------------------------------------
# Helpers
# --------------------------------------------------
async def run_with_timeout(fn, timeout=120):
    return await asyncio.wait_for(asyncio.to_thread(fn), timeout)

def chunk_list(items, size=10):
    for i in range(0, len(items), size):
        yield items[i:i + size]

def get_pdf_page_size(pdf_bytes: bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    page = reader.pages[0]
    box = page.mediabox

    width_pt = float(box.width)
    height_pt = float(box.height)

    return width_pt, height_pt  # points

async def apply_cooldown(job_id: str, seconds: int):
    meta = JOB_STATUS[job_id]["__meta__"]
    meta["cooldown"] = True

    for remaining in range(seconds, 0, -1):
        meta["cooldown_remaining"] = remaining
        await asyncio.sleep(1)

    meta["cooldown"] = False
    meta["cooldown_remaining"] = 0


# --------------------------------------------------
# Background worker
# --------------------------------------------------
async def process_batch(job_id: str, files: List[Dict]):
    credentials = ServicePrincipalCredentials(
        client_id=ADOBE_CLIENT_ID,
        client_secret=ADOBE_CLIENT_SECRET,
    )
    pdf_services = PDFServices(credentials)
    zip_buffer = io.BytesIO()
    COOLDOWN_SECONDS = 30
    merged_docx_items: List[bytes] = []
    chunks = list(chunk_list(files, 5))
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_writer:
        for batch_index, chunk in enumerate(chunks, start=1):
            for f in chunk:
                name = f["name"]
                JOB_STATUS[job_id][name]["status"] = (
                    f"Batch {batch_index}/{len(chunks)} – Preparing"
                )
                JOB_STATUS[job_id][name]["progress"] = 5
                pdf_bytes = f["bytes"]
                out_name = os.path.splitext(name)[0] + ".docx"
                try:
                    if not pdf_bytes:
                        raise ValueError("Empty file")
                    JOB_STATUS[job_id][name]["status"] = "Uploading"
                    JOB_STATUS[job_id][name]["progress"] = 25
                    pdf_stream = io.BytesIO()
                    pdf_stream.write(pdf_bytes)
                    pdf_stream.seek(0)
                    input_asset = pdf_services.upload(
                        input_stream=pdf_stream,
                        mime_type=PDFServicesMediaType.PDF,
                    )
                    JOB_STATUS[job_id][name]["status"] = "Converting"
                    JOB_STATUS[job_id][name]["progress"] = 55
                    export_job = ExportPDFJob(
                        input_asset=input_asset,
                        export_pdf_params=ExportPDFParams(
                            target_format=ExportPDFTargetFormat.DOCX
                        ),
                    )
                    location = await run_with_timeout(
                        lambda: pdf_services.submit(export_job)
                    )
                    job_result = await run_with_timeout(
                        lambda: pdf_services.get_job_result(
                            location, ExportPDFResult
                        )
                    )
                    JOB_STATUS[job_id][name]["status"] = "Finalizing"
                    JOB_STATUS[job_id][name]["progress"] = 90
                    result_asset = job_result.get_result().get_asset()
                    stream_asset = pdf_services.get_content(result_asset)
                    stream = stream_asset.get_input_stream()
                    if isinstance(stream, (bytes, bytearray)):
                        docx_bytes = stream
                    else:
                        docx_bytes = stream.read()
                    if not docx_bytes:
                        raise RuntimeError("Empty DOCX output")
                    zip_writer.writestr(out_name, docx_bytes)
                    merged_docx_items.append({
                        "docx": docx_bytes,
                        "page_size": f["page_size"],
                    })
                    JOB_STATUS[job_id][name]["status"] = "Converted ✔"
                    JOB_STATUS[job_id][name]["progress"] = 100
                    JOB_STATUS[job_id][name]["output"] = True
                except Exception as e:
                    error_msg = str(e)
                    print(f"[ERROR] {name}: {error_msg}")
                    JOB_STATUS[job_id][name]["status"] = f"Failed ❌"
                    JOB_STATUS[job_id][name]["progress"] = 0
                    JOB_STATUS[job_id][name]["output"] = False
                    await apply_cooldown(job_id, 20)
                    if "Request could not be completed" in error_msg:
                        JOB_STATUS[job_id][name]["status"] = "Retrying…"
                        JOB_STATUS[job_id][name]["progress"] = 20
                        await asyncio.sleep(5)
                        try:
                            # recreate stream (important)
                            pdf_stream = io.BytesIO(pdf_bytes)
                            input_asset = pdf_services.upload(
                                input_stream=pdf_stream,
                                mime_type=PDFServicesMediaType.PDF,
                            )
                            export_job = ExportPDFJob(
                                input_asset=input_asset,
                                export_pdf_params=ExportPDFParams(
                                    target_format=ExportPDFTargetFormat.DOCX
                                ),
                            )
                            location = await run_with_timeout(
                                lambda: pdf_services.submit(export_job)
                            )
                            job_result = await run_with_timeout(
                                lambda: pdf_services.get_job_result(
                                    location, ExportPDFResult
                                )
                            )
                            result_asset = job_result.get_result().get_asset()
                            stream_asset = pdf_services.get_content(result_asset)
                            stream = stream_asset.get_input_stream()
                            docx_bytes = stream if isinstance(stream, (bytes, bytearray)) else stream.read()
                            if not docx_bytes:
                                raise RuntimeError("Empty DOCX output")
                            zip_writer.writestr(out_name, docx_bytes)
                            merged_docx_items.append({
                                "docx": docx_bytes,
                                "page_size": f["page_size"],
                            })
                            JOB_STATUS[job_id][name]["status"] = "Converted ✔"
                            JOB_STATUS[job_id][name]["progress"] = 100
                            JOB_STATUS[job_id][name]["output"] = True
                            continue   # 🔴 VERY IMPORTANT
                        except Exception as e2:
                            error_msg2 = str(e2)
                            print(f"[ERROR] Retry failed for {name}: {error_msg2}")
                            JOB_STATUS[job_id][name]["status"] = f"Failed ❌"
                            JOB_STATUS[job_id][name]["progress"] = 0
                            JOB_STATUS[job_id][name]["output"] = False
                    # --------------------------------------------------
        # Merge all DOCX into ONE combined document
        # --------------------------------------------------
        if len(merged_docx_items) >= 2:
            try:
                combined_bytes = merge_docx_bytes(merged_docx_items)

                combined_name = (
                    JOB_STATUS[job_id]["__meta__"]["folder_name"]
                    .replace(" ", "_")
                    + "_COMBINED.docx"
                )
                zip_writer.writestr(combined_name, combined_bytes)
                # 👇 expose for UI / status
                JOB_STATUS[job_id]["__meta__"]["combined"] = combined_name
            except Exception as e:
                print("[WARN] DOCX merge failed:", e)
            # ---- cooldown after every 10 files ----
            meta = JOB_STATUS[job_id]["__meta__"]
            if batch_index < len(chunks):
                for remaining in range(COOLDOWN_SECONDS, 0, -1):
                    meta["cooldown"] = True
                    meta["cooldown_remaining"] = remaining
                    await asyncio.sleep(10)
                meta["cooldown"] = False
                meta["cooldown_remaining"] = 0
    zip_buffer.seek(0)
    JOB_ZIPS[job_id] = zip_buffer.getvalue()

# --------------------------------------------------
# Start batch
# --------------------------------------------------
@app.post("/convert/batch")
async def start_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    job_id = str(uuid.uuid4())
    JOB_STATUS[job_id] = {}
    payloads = []
    folder_name = None
    for f in files:
        data = await f.read()
        # 👇 extract folder name once
        if folder_name is None and "/" in f.filename:
            folder_name = f.filename.split("/", 1)[0]
        basename = os.path.basename(f.filename)
        JOB_STATUS[job_id][basename] = {
            "name": basename,
            "status": "Queued",
            "progress": 0,
            "output": False,
        }
        payloads.append({
            "name": basename,
            "bytes": data,
            "page_size": get_pdf_page_size(data),
        })
    # Fallback if user uploaded loose files
    if not folder_name:
        folder_name = "converted_batch"
    # 🔐 Store it
    JOB_STATUS[job_id]["__meta__"] = {
        "folder_name": folder_name
    }
    background_tasks.add_task(process_batch, job_id, payloads)
    return {"job_id": job_id, "folder": folder_name}

# --------------------------------------------------
# Poll status
# --------------------------------------------------
@app.get("/convert/status/{job_id}")
def get_status(job_id: str):
    if job_id not in JOB_STATUS:
        raise HTTPException(404, "Job not found")
    return list(JOB_STATUS[job_id].values())

# --------------------------------------------------
# Download ZIP
# --------------------------------------------------
@app.get("/convert/download/{job_id}")
def download_zip(job_id: str, include_merged: int = Query(1)):
    if job_id not in JOB_ZIPS:
        raise HTTPException(404, "ZIP not ready")
    zip_bytes = JOB_ZIPS[job_id]
    if include_merged == 0:
        # remove combined docx from zip
        zip_in = io.BytesIO(zip_bytes)
        zip_out = io.BytesIO()
        with zipfile.ZipFile(zip_in, "r") as zin, \
             zipfile.ZipFile(zip_out, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename.endswith("_COMBINED.docx"):
                    continue
                zout.writestr(item, zin.read(item.filename))
        zip_bytes = zip_out.getvalue()
    folder_name = JOB_STATUS[job_id].get("__meta__", {}).get(
        "folder_name", "converted_batch"
    )
    safe_name = folder_name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{safe_name}_converted.zip"'
            )
        },
    )


@app.get("/convert/summary/{job_id}")
def get_summary(job_id: str):
    if job_id not in JOB_STATUS:
        raise HTTPException(404, "Job not found")
    files = [
        f for k, f in JOB_STATUS[job_id].items()
        if not k.startswith("__")
    ]
    total = len(files)
    converted = sum(1 for f in files if f.get("output") is True)
    failed = sum(
        1 for f in files
        if f.get("status", "").startswith("Failed")
    )
    return {
        "total": total,
        "converted": converted,
        "failed": failed,
        "finished": converted + failed,
    }

def merge_docx_bytes(docx_items: List[Dict]) -> bytes:
    """
    docx_items = [
      {
        "docx": bytes,
        "page_size": (width_pt, height_pt)
      },
      ...
    ]
    """

    if not docx_items:
        raise RuntimeError("No DOCX files to merge")

    first = docx_items[0]
    master = Document(io.BytesIO(first["docx"]))
    composer = Composer(master)

    # Apply size to first section
    _apply_page_size(master.sections[0], first["page_size"])

    for item in docx_items[1:]:
        # 🔴 NEW SECTION (not page break)
        section = master.add_section(WD_SECTION.NEW_PAGE)
        _apply_page_size(section, item["page_size"])

        composer.append(Document(io.BytesIO(item["docx"])))

    out = io.BytesIO()
    composer.save(out)
    out.seek(0)
    return out.read()

def _apply_page_size(section, page_size):
    width_pt, height_pt = page_size

    # Orientation
    if width_pt > height_pt:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width = Pt(width_pt)
        section.page_height = Pt(height_pt)
    else:
        section.orientation = WD_ORIENT.PORTRAIT
        section.page_width = Pt(width_pt)
        section.page_height = Pt(height_pt)

    # 🔴 CRITICAL: remove margins
    section.top_margin = Pt(12)
    section.bottom_margin = Pt(12)
    section.left_margin = Pt(12)
    section.right_margin = Pt(12)
