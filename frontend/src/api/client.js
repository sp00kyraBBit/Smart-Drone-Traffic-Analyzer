import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
});

export async function uploadVideo(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return response.data;
}

export async function startProcessing(jobId) {
  const response = await api.post(`/api/process/${jobId}`);
  return response.data;
}

export async function getJobStatus(jobId) {
  const response = await api.get(`/api/status/${jobId}`);
  return response.data;
}

export async function getJobResults(jobId) {
  const response = await api.get(`/api/results/${jobId}`);
  return response.data;
}

export function buildAbsoluteUrl(path) {
  return `${API_BASE_URL}${path}`;
}

export default api;