import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useMemo } from "react";
import { apiGet } from "@/api";
import { Button } from "@/components/Button";
import { Grid } from "@/components/Grid";
import { Modal } from "@/components/Modal";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { DEFAULT_METRICS, METRICS, type Metric } from "@/metrics";
import type { VehicleInfo } from "@/types";
import { MetricCard } from "./MetricCard";
import styles from "./Monitors.module.css";

const cx = classNames.bind(styles);

export type MetricSelectionProps = {
	open: boolean;
	onClose: () => void;
};

export function MetricSelection({ open, onClose }: MetricSelectionProps) {
	const [selectedVin] = useLocalStorage("selected-vin");
	const [metricsSelection, setMetricsSelection] =
		useLocalStorage("metrics-selection");

	const { data: vehicles = [] } = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const supportedMetrics = useMemo(() => {
		return vehicles.find((v) => v.vin === selectedVin)?.supported_metrics;
	}, [vehicles, selectedVin]);

	const defaultSelection = useMemo(() => {
		return Object.fromEntries(
			METRICS.map((m) => [
				m,
				DEFAULT_METRICS.has(m) && supportedMetrics?.includes(m),
			]),
		) as Record<Metric, boolean>;
	}, [supportedMetrics]);

	useEffect(() => {
		if (!supportedMetrics) {
			return;
		}
		if (!metricsSelection) {
			setMetricsSelection(defaultSelection);
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
	}, [
		defaultSelection,
		metricsSelection,
		setMetricsSelection,
		supportedMetrics,
	]);

	return (
		<Modal open={open} onClose={onClose}>
			<div className={cx("metrics-selection")}>
				<Button
					onClick={() => setMetricsSelection(undefined)}
					text="Reset"
					disabled={
						JSON.stringify(metricsSelection) ===
						JSON.stringify(defaultSelection)
					}
				/>
				{supportedMetrics && (
					<Grid
						Item={MetricCard}
						data={supportedMetrics.map((metric) => ({ metric, key: metric }))}
						className={cx("metrics-grid")}
					/>
				)}
			</div>
		</Modal>
	);
}
