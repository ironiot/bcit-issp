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
	"selected-metrics": Record<Metric, boolean>;
};
type Key = keyof Storage;

const KEYS = ["selected-vin", "selected-metrics"] as const satisfies Key[];

type LocalStorage = {
	get: <K extends Key>(key: K) => Storage[K] | undefined;
	set: <K extends Key>(key: K, value: Storage[K]) => void;
};

const LocalStorageContext = createContext<LocalStorage | null>(null);

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

	const set = useCallback(<K extends Key>(key: K, value: Storage[K]) => {
		setStorage((prev) => ({ ...prev, [key]: value }));
		localStorage.setItem(key, JSON.stringify(value));
	}, []);

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
		(value: Storage[K]) => set(key, value),
		[set, key],
	);

	return [value, setValue] as const;
}
