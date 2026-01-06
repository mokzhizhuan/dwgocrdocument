import axios from "axios";
import { API_BASE } from "./config";

export async function convertFile(file: File) {
  const form = new FormData();
  form.append("file", file);

  const res = await axios.post(`${API_BASE}/convert`, form, {
    responseType: "blob",
  });

  return res.data; // DOCX blob
}
