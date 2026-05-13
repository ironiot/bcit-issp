import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/api";
import { Grid } from "@/components/Grid";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import { Vehicle } from "./Vehicle";

export function Vehicles() {
	const { data: vehicles = [] } = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const { set } = useLocalStorage();

	return (
		<Grid
			Item={Vehicle}
			data={vehicles.map((v) => ({ ...v, key: v.vin }))}
			itemWidth={300}
			onClickItem={(vehicle) => set("selected-vin", vehicle.vin)}
		/>
	);
}
