import type React from "react";
import { Navigate } from "react-router-dom";
import { useLocalStorage } from "@/hooks/LocalStorage";

export function useIsConfigMissing() {
	const [selectedVin] = useLocalStorage("selected-vin");
	const [metricsSelection] = useLocalStorage("metrics-selection");

	return (
		!selectedVin ||
		!metricsSelection ||
		!Object.values(metricsSelection).some((v) => v)
	);
}

type Props = { Renderer: React.FC };
export function ConfigValidator({ Renderer }: Props) {
	const isConfigMissing = useIsConfigMissing();
	return isConfigMissing ? <Navigate to="/" replace /> : <Renderer />;
}
