const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
export class RequestError extends Error { constructor(message:string, public status:number){ super(message); } }
export async function api<T>(path:string, options:RequestInit = {}):Promise<T> {
  const response = await fetch(`${API}${path}`, { credentials:"include", ...options, headers: options.body instanceof FormData ? options.headers : {"Content-Type":"application/json", ...options.headers} });
  if (!response.ok) { const body = await response.json().catch(()=>({})); throw new RequestError(body?.error?.message ?? "Request failed", response.status); }
  return response.status === 204 ? undefined as T : response.json();
}
