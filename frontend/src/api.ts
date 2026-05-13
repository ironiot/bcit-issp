const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export function apiUrl(path: string): string {
	const p = path.startsWith("/") ? path : `/${path}`;
	return `${API_BASE}${p}`;
}

export async function apiGet<T>(path: string): Promise<T> {
	const res = await fetch(apiUrl(path));
	if (!res.ok) {
		const text = await res.text();
		throw new Error(`${res.status} ${res.statusText}: ${text.slice(0, 240)}`);
	}
	return res.json() as Promise<T>;
}
