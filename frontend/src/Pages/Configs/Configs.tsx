import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useMemo } from "react";
import { apiGet } from "@/api";
import { Grid } from "@/components/Grid";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { Metric } from "@/metrics";
import type { VehicleInfo } from "@/types";
import styles from "./Configs.module.css";

const cx = classNames.bind(styles);

import { MetricCard } from "./MetricCard";
import { VehicleCard } from "./VehicleCard";

export function Configs() {
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

	const supportedMetrics = useMemo(() => {
		return vehicles.find((v) => v.vin === selectedVin)?.supported_metrics;
	}, [vehicles, selectedVin]);

	const [metricsSelection, setMetricsSelection] =
		useLocalStorage("metrics-selection");

	useEffect(() => {
		if (!metricsSelection || !supportedMetrics) {
			return;
		}
		// Remove unsupported metrics from selectedMetrics
		// (when user switches to a different vehicle with different supported metrics)
		const filteredMetrics = Object.fromEntries(
			Object.entries(metricsSelection).map(([metric, isSelected]) => [
				metric,
				isSelected && supportedMetrics.includes(metric as any),
			]),
		) as Record<Metric, boolean>;
		setMetricsSelection(filteredMetrics);
	}, [supportedMetrics, setMetricsSelection, metricsSelection]);

	return (
		<div className={cx("configs")}>
			<Grid
				Item={VehicleCard}
				data={vehicles.map((v) => ({ ...v, key: v.vin }))}
			/>
			{supportedMetrics && (
				<Grid
					Item={MetricCard}
					data={supportedMetrics?.map((metric) => ({ metric, key: metric }))}
				/>
			)}
		</div>
	);
}
