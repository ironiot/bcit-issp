import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { apiGet } from "@/api";
import { Grid } from "@/components/Grid";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import { VehicleCard } from "./VehicleCard";

export function Vehicles() {
	const { data: vehicles = [] } = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const [selectedVin, selectVin] = useLocalStorage("selected-vin");
	useEffect(() => {
		// in case localStorage is stale (vehicle no longer exists)
		if (
			selectedVin &&
			vehicles.length > 0 &&
			!vehicles.some((v) => v.vin === selectedVin)
		) {
			selectVin("");
		}
	}, [selectedVin, selectVin, vehicles]);

	return (
		<Grid
			Item={VehicleCard}
			data={vehicles.map((v) => ({ ...v, key: v.vin }))}
		/>
	);
}
