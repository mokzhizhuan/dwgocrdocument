import os
from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
from adobe.pdfservices.operation.pdf_services import PDFServices
from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
from adobe.pdfservices.operation.pdfjobs.jobs.export_pdf_job import ExportPDFJob
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_params import ExportPDFParams
from adobe.pdfservices.operation.pdfjobs.params.export_pdf.export_pdf_target_format import ExportPDFTargetFormat
from adobe.pdfservices.operation.pdfjobs.result.export_pdf_result import ExportPDFResult
from adobe.pdfservices.operation.io.stream_asset import StreamAsset
from adobe.pdfservices.operation.exception.exceptions import (
    ServiceApiException,
    ServiceUsageException,
    SdkException,
)

def main():
    client_id = os.getenv("PDF_SERVICES_CLIENT_ID")
    client_secret = os.getenv("PDF_SERVICES_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("❌ Env vars not set: PDF_SERVICES_CLIENT_ID / PDF_SERVICES_CLIENT_SECRET")
        return

    print("Using CLIENT_ID:", client_id)

    # Use any small test PDF in your folder
    input_path = "test.pdf"
    if not os.path.exists(input_path):
        print(f"❌ No {input_path} found. Put a small PDF as test.pdf next to this script.")
        return

    with open(input_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        creds = ServicePrincipalCredentials(
            client_id=client_id,
            client_secret=client_secret,
        )
        pdf_services = PDFServices(credentials=creds)

        # Upload PDF
        input_asset = pdf_services.upload(
            input_stream=pdf_bytes,
            mime_type=PDFServicesMediaType.PDF,
        )

        export_params = ExportPDFParams(
            target_format=ExportPDFTargetFormat.DOCX
        )
        export_job = ExportPDFJob(
            input_asset=input_asset,
            export_pdf_params=export_params,
        )

        location = pdf_services.submit(export_job)
        print("🔁 Job submitted, location:", location)

        result: ExportPDFResult = pdf_services.get_job_result(
            location, ExportPDFResult
        )
        result_asset = result.get_result().get_asset()
        stream_asset: StreamAsset = pdf_services.get_content(result_asset)
        docx_bytes = stream_asset.get_input_stream()

        output_path = "test_out.docx"
        with open(output_path, "wb") as f:
            f.write(docx_bytes)

        print("✅ Credentials valid. Converted PDF → DOCX saved as", output_path)

    except (ServiceApiException, ServiceUsageException, SdkException) as e:
        print("❌ Adobe API error. Credentials might be wrong or quota exceeded.")
        print("   Error:", e)
    except Exception as e:
        print("❌ Unexpected error:", e)

if __name__ == "__main__":
    main()
