import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useMemo,
	useState,
} from "react";
import type { Metric } from "@/metrics";

type Storage = {
	"selected-vin": string;
	"metrics-selection": Record<Metric, boolean>;
};
type Key = keyof Storage;

const KEYS = ["selected-vin", "metrics-selection"] as const satisfies Key[];

type LocalStorageContext = {
	get: <K extends Key>(key: K) => Storage[K] | undefined;
	set: <K extends Key>(key: K, value: Storage[K] | undefined) => void;
};

const LocalStorageContext = createContext<LocalStorageContext | null>(null);

export function LocalStorageProvider({ children }: { children: ReactNode }) {
	const [storage, setStorage] = useState(() =>
		KEYS.reduce<Partial<Storage>>((acc, key) => {
			const storedValue = localStorage.getItem(key);
			if (storedValue !== null) {
				try {
					acc[key] = JSON.parse(storedValue);
				} catch (e) {
					console.error(`Error parsing localStorage key "${key}":`, e);
				}
			}
			return acc;
		}, {}),
	);

	const get = useCallback(
		<K extends Key>(key: K) => {
			return storage[key] as Storage[K] | undefined;
		},
		[storage],
	);

	const set = useCallback(
		<K extends Key>(key: K, value: Storage[K] | undefined) => {
			setStorage((prev) => ({ ...prev, [key]: value }));

			if (value === undefined) {
				localStorage.removeItem(key);
			} else {
				localStorage.setItem(key, JSON.stringify(value));
			}
		},
		[],
	);

	return (
		<LocalStorageContext.Provider value={{ get, set }}>
			{children}
		</LocalStorageContext.Provider>
	);
}

export function useLocalStorage<K extends Key>(key: K) {
	const context = useContext(LocalStorageContext);
	if (!context) {
		throw new Error(
			"useLocalStorage must be used within a LocalStorageProvider",
		);
	}

	const { get, set } = context;

	const value = useMemo(() => get(key), [get, key]);
	const setValue = useCallback(
		(value: Storage[K] | undefined) => set(key, value),
		[set, key],
	);

	return [value, setValue] as const;
}
