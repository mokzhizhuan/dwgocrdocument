export async function uploadLocalDwgAndConvert(file: File): Promise<Blob> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("http://localhost:8000/convert_dwg", {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "DWG→PDF failed.");
  }

  return await res.blob();  // This will be the PDF file
}
