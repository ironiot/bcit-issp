import { useQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { apiGet } from "@/api";
import { Grid } from "@/components/Grid";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import { MetricCard } from "./MetricCard";

export function Configs() {
	const [selectedVin] = useLocalStorage("selected-vin");
	const { data: vehicles = [] } = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const data = useMemo(() => {
		return vehicles
			.find((v) => v.vin === selectedVin)
			?.supported_metrics.map((metric) => ({ metric, key: metric }));
	}, [vehicles, selectedVin]);

	if (!data) {
		return null;
	}

	return <Grid data={data} Item={MetricCard} />;
}
