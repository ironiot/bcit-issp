import {
	createContext,
	type ReactNode,
	useCallback,
	useContext,
	useState,
} from "react";

type LocalStorageKey = "selected-vin";

type LocalStorage = {
	get: <T>(key: LocalStorageKey, initialValue: T) => T;
	set: <T>(key: LocalStorageKey, value: T) => void;
};

const LocalStorageContext = createContext<LocalStorage | null>(null);

// To consolate all keys in one place, prevent typos or inconsistencies

export function LocalStorageProvider({ children }: { children: ReactNode }) {
	const [storage, setStorage] = useState<Record<string, unknown>>({});

	const get = useCallback(
		<T,>(key: LocalStorageKey, initialValue: T) => {
			if (key in storage) {
				return storage[key] as T;
			}

			const storedValue = localStorage.getItem(key);
			if (storedValue !== null) {
				try {
					const parsedValue = JSON.parse(storedValue);
					setStorage((prev) => ({ ...prev, [key]: parsedValue }));
					return parsedValue as T;
				} catch (e) {
					console.error(`Error parsing localStorage key "${key}":`, e);
				}
			}

			return initialValue;
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

export function useLocalStorage() {
	const context = useContext(LocalStorageContext);
	if (!context) {
		throw new Error(
			"useLocalStorage must be used within a LocalStorageProvider",
		);
	}
	return context;
}
