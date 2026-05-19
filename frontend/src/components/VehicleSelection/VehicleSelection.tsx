import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useState } from "react";
import { apiGet } from "@/api";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { Grid } from "@/components/Grid";
import { Modal } from "@/components/Modal";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import { VehicleCard } from "./VehicleCard";
import styles from "./VehicleSelection.module.css";

const cx = classNames.bind(styles);

export function VehicleSelection({ className }: { className?: string }) {
	const [selectedVin, selectVin] = useLocalStorage("selected-vin");

	const {
		data: vehicles = [],
		isLoading,
		error,
	} = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	console.log(vehicles);

	useEffect(() => {
		// in case localStorage is stale (vehicle no longer exists)
		if (
			selectedVin &&
			vehicles.length > 0 &&
			!vehicles.some((v) => v.vin === selectedVin)
		) {
			selectVin("");
		}
		// auto select if there's only one vehicle
		else if (vehicles.length === 1) {
			selectVin(vehicles[0].vin);
		}
	}, [selectedVin, selectVin, vehicles]);

	const vehicle = vehicles.find((v) => v.vin === selectedVin);

	const [isVehicleListOpen, setOpenVehicleList] = useState(false);

	return (
		<Card className={cx("vehicle-selection", className)} aria-label="Vehicle">
			<div className={cx("header")}>
				<h2>Vehicle</h2>
				{vehicles.length > 1 && (
					<Button onClick={() => setOpenVehicleList(true)} text="Select" />
				)}
			</div>
			{isLoading ? (
				<p className="muted">Loading vehicles…</p>
			) : error ? (
				<p className="muted">Error loading vehicle data.</p>
			) : !vehicle ? (
				<p className="muted">No vehicle selected.</p>
			) : (
				<dl className={cx("vehicle-grid")}>
					<div>
						<dt>VIN</dt>
						<dd>{vehicle.vin}</dd>
					</div>
					<div>
						<dt>Model</dt>
						<dd>{vehicle.model ?? "—"}</dd>
					</div>
					<div>
						<dt>Body</dt>
						<dd>{vehicle.body_type ?? "—"}</dd>
					</div>
					<div>
						<dt>Fuel</dt>
						<dd>{vehicle.fuel_type ?? "—"}</dd>
					</div>
					<div>
						<dt>Drive cycles</dt>
						<dd>{vehicle.drive_cycles_count}</dd>
					</div>
					<div>
						<dt>Distance (stored)</dt>
						<dd>
							{typeof vehicle.distance === "number"
								? `${vehicle.distance.toFixed(1)} km`
								: "—"}
						</dd>
					</div>
					<div>
						<dt>Active DTCs</dt>
						<dd>
							{vehicle.active_dtcs?.filter(Boolean).length
								? vehicle.active_dtcs.filter(Boolean).join(", ")
								: "None"}
						</dd>
					</div>
					<div>
						<dt>Last sample</dt>
						<dd>
							{vehicle.last_measure ? formatTime(vehicle.last_measure) : "—"}
						</dd>
					</div>
				</dl>
			)}
			<Modal open={isVehicleListOpen} onClose={() => setOpenVehicleList(false)}>
				<Grid
					Item={VehicleCard}
					data={vehicles.map((v) => ({ ...v, key: v.vin }))}
				/>
			</Modal>
		</Card>
	);
}

function formatTime(iso: string): string {
	try {
		return new Date(iso).toLocaleString(undefined, {
			month: "short",
			day: "numeric",
			hour: "2-digit",
			minute: "2-digit",
		});
	} catch {
		return iso;
	}
}
