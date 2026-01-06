import axios from "axios";
import { API_BASE } from "./config";

export async function convertFile(file: File) {
  const form = new FormData();
  form.append("file", file);

  const response = await axios.post(`${API_BASE}/convert`, form, {
    responseType: "blob",         // IMPORTANT!
  });

  // Extract filename from FastAPI response header
  const disposition = response.headers["content-disposition"];
  let filename = "converted.docx";

  if (disposition) {
    const match = disposition.match(/filename="(.+)"/);
    if (match) filename = match[1];
  }

  return { blob: response.data, filename };
}