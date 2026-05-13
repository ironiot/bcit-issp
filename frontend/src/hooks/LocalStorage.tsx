import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useMemo,
	useState,
} from "react";

// To consolate all keys in one place, prevent typos or inconsistencies
const keys = ["selected-vin"] as const;
type LocalStorageKey = (typeof keys)[number];

type LocalStorage = {
	get: <T>(key: LocalStorageKey) => T | undefined;
	set: <T>(key: LocalStorageKey, value: T) => void;
};

const LocalStorageContext = createContext<LocalStorage | null>(null);

export function LocalStorageProvider({ children }: { children: ReactNode }) {
	const [storage, setStorage] = useState<Record<string, unknown>>(() =>
		keys.reduce(
			(acc, key) => {
				const storedValue = localStorage.getItem(key);
				if (storedValue !== null) {
					try {
						acc[key] = JSON.parse(storedValue);
					} catch (e) {
						console.error(`Error parsing localStorage key "${key}":`, e);
					}
				}
				return acc;
			},
			{} as Record<string, unknown>,
		),
	);

	const get = useCallback(
		<T,>(key: LocalStorageKey) => {
			if (key in storage) {
				return storage[key] as T;
			}
		},
		[storage],
	);

	const set = useCallback(<T,>(key: LocalStorageKey, value: T) => {
		setStorage((prev) => ({ ...prev, [key]: value }));
		localStorage.setItem(key, JSON.stringify(value));
	}, []);

	return (
		<LocalStorageContext.Provider value={{ get, set }}>
			{children}
		</LocalStorageContext.Provider>
	);
}

export function useLocalStorage<T = string>(key: LocalStorageKey) {
	const context = useContext(LocalStorageContext);
	if (!context) {
		throw new Error(
			"useLocalStorage must be used within a LocalStorageProvider",
		);
	}

	const { get, set } = context;

	const value = useMemo(() => get<T>(key), [get, key]);
	const setValue = useCallback((value: T) => set(key, value), [set, key]);

	return [value, setValue] as const;
}
