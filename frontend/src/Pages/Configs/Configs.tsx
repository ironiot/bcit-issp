import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useMemo } from "react";
import { apiGet } from "@/api";
import { Grid } from "@/components/Grid";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { DEFAULT_METRICS, METRICS, type Metric } from "@/metrics";
import type { VehicleInfo } from "@/types";
import styles from "./Configs.module.css";

const cx = classNames.bind(styles);

import { Button } from "@/components/Button";
import { MetricCard } from "./MetricCard";
import { VehicleCard } from "./VehicleCard";

export function Configs() {
	const { data: vehicles = [], refetch: reloadVehicles } = useQuery({
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
		// auto select if there's only one vehicle
		else if (vehicles.length === 1) {
			selectVin(vehicles[0].vin);
		}
	}, [selectedVin, selectVin, vehicles]);

	const supportedMetrics = useMemo(() => {
		return vehicles.find((v) => v.vin === selectedVin)?.supported_metrics;
	}, [vehicles, selectedVin]);

	const [metricsSelection, setMetricsSelection] =
		useLocalStorage("metrics-selection");

	useEffect(() => {
		if (!supportedMetrics) {
			return;
		}

		if (!metricsSelection) {
			const defaultMetrics = Object.fromEntries(
				METRICS.map((m) => [
					m,
					DEFAULT_METRICS.has(m) && supportedMetrics.includes(m),
				]),
			) as Record<Metric, boolean>;
			setMetricsSelection(defaultMetrics);
			return;
		}

		// when user switches to a different vehicle with different supported metrics
		if (
			!Object.entries(metricsSelection)
				.filter(([_, isSelected]) => isSelected)
				.every(([metric]) => supportedMetrics.includes(metric as Metric))
		) {
			const filteredMetrics = Object.fromEntries(
				Object.entries(metricsSelection).map(([metric, isSelected]) => [
					metric,
					isSelected && supportedMetrics.includes(metric as any),
				]),
			) as Record<Metric, boolean>;
			setMetricsSelection(filteredMetrics);
		}
	}, [supportedMetrics, setMetricsSelection, metricsSelection]);

	return (
		<div className={cx("configs")}>
			<div className={cx("Select vehicle")}>
				<div className={cx("header")}>
					<div>
						<h2>Vehicle selection</h2>
						<span>Select which vehicle to monitor and display data for</span>
					</div>
					<Button
						text="Refresh"
						onClick={() => reloadVehicles()}
						disabled={!selectedVin}
					/>
				</div>
				<Grid
					Item={VehicleCard}
					data={vehicles.map((v) => ({ ...v, key: v.vin }))}
				/>
			</div>

			{supportedMetrics && (
				<div className={cx("metrics")}>
					<div className={cx("header")}>
						<div>
							<h2>Metrics selection</h2>
							<span>Filter which metrics to query and display</span>
						</div>
						<Button
							onClick={() => setMetricsSelection(undefined)}
							text="Reset"
						/>
					</div>
					<Grid
						Item={MetricCard}
						data={supportedMetrics?.map((metric) => ({ metric, key: metric }))}
					/>
				</div>
			)}
		</div>
	);
}
