// ─── Flask API stubs ──────────────────────────────────────────────────────────
// Replace mock imports with these calls once the Flask backend is wired up.
//
// const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
const BASE_URL = "http://127.0.0.1:5000";

export async function apiFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;

  const config = {
    method: options.method || "GET",
    ...options,
  };

  if (options.body) {
    config.headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    config.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, config);
  if (!response.ok) throw new Error("API request failed");
  return response.json();
}

//
// export const fetchVendorRisk = async (vendorId) => {
//   const res = await fetch(`${BASE_URL}/api/vendor/${vendorId}/risk`)
//   if (!res.ok) throw new Error(res.statusText)
//   return res.json()
// }
//
// export const fetchRiskForecast = async (vendorId) => {
//   const res = await fetch(`${BASE_URL}/api/vendor/${vendorId}/forecast`)
//   if (!res.ok) throw new Error(res.statusText)
//   return res.json()
// }
//
// export const fetchVendorComparison = async (vendorIdA, vendorIdB) => {
//   const res = await fetch(`${BASE_URL}/api/compare?a=${vendorIdA}&b=${vendorIdB}`)
//   if (!res.ok) throw new Error(res.statusText)
//   return res.json()
// }
//
// export const fetchLeadingIndicators = async (vendorId) => {
//   const res = await fetch(`${BASE_URL}/api/vendor/${vendorId}/indicators`)
//   if (!res.ok) throw new Error(res.statusText)
//   return res.json()
// }
//
export const fetchHelloWorld = async () => {
  const res = await fetch(`${BASE_URL}/api/hello-world`);
  if (!res.ok) throw new Error(res.status);
  return res.json();
};

// ─── Using mock data for now ──────────────────────────────────────────────────
export { vendors, vendorList } from "../data/mockData";
