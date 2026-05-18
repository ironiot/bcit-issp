import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { apiGet } from "@/api";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import styles from "./VehicleSummary.module.css";

const cx = classNames.bind(styles);

interface VehicleSummaryProps {
	className?: string;
}

export function VehicleSummary({ className }: VehicleSummaryProps) {
	const [selectedVin] = useLocalStorage("selected-vin");

	const {
		data: vehicles = [],
		isLoading,
		error,
	} = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const vehicle = vehicles.find((v) => v.vin === selectedVin);

	return (
		<Card className={cx("vehicle-summary", className)} aria-label="Vehicle">
			<h2>Vehicle</h2>
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
