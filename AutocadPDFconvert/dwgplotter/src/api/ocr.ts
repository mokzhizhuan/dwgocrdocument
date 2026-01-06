import axios from "axios";
import { API_BASE } from "./config";

export async function fetchWorkflows() {
  const res = await axios.get(`${API_BASE}/workflows`);
  return res.data; // array of workflows from FRS
}

export async function ocrUpload(file: File, workflow: string) {
  const form = new FormData();
  form.append("file", file);
  form.append("workflow_name", workflow);

  const res = await axios.post(`${API_BASE}/ocr`, form, {
    responseType: "blob",
  });

  return res.data; // PDF blob
}
