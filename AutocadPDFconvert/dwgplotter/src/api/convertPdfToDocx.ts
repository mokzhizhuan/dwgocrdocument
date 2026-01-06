import axios from "axios";
import { API_BASE_URL } from "../config";

export async function convertPdfToDocx(
  file: File
): Promise<{ blob: Blob; filename: string }> {
  const form = new FormData();
  form.append("file", file);

  const response = await axios.post(`${API_BASE_URL}/convert/pdf-to-docx`, form, {
    responseType: "blob",
  });

  // --- Build filename from original PDF name ---
  const originalName = file.name; // e.g. "LTG_DT_001 - TYPICAL LIGHTING DETAIL NO. 1.pdf"
  const base = originalName.replace(/\.pdf$/i, ""); // strip .pdf (case-insensitive)
  let filename = `${base}_convert.docx`;          // e.g. "... 1_convert.docx"

  // If server also sends a filename, you can optionally override:
  const cd = response.headers["content-disposition"] as string | undefined;
  if (cd) {
    const match = cd.match(/filename="([^"]+)"/);
    if (match && match[1]) {
      filename = match[1];
    }
  }

  return { blob: response.data, filename };
}
