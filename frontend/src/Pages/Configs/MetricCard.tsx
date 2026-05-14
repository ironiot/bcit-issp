import { SvgIcon } from "@mui/material";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import {
	DEFAULT_ENABLED_METRICS,
	METRIC_ICONS,
	METRICS,
	METRICS_LABELS,
	type Metric,
} from "@/metrics";

type Props = { metric: Metric };
export function MetricCard({ metric }: Props) {
	const [
		selectedMetrics = METRICS.reduce(
			(acc, m) =>
				Object.assign(acc, { [m]: DEFAULT_ENABLED_METRICS.has(m) }, acc),
			{} as Record<Metric, boolean>,
		),
		setSelectedMetrics,
	] = useLocalStorage("selected-metrics");

	const toggleSelection = () =>
		setSelectedMetrics({
			...selectedMetrics,
			[metric]: !selectedMetrics[metric],
		});

	return (
		<Card
			style={{
				display: "flex",
				flexDirection: "column",
				alignItems: "center",
				justifyContent: "center",
				width: 96,
				height: 160,
				textAlign: "center",
			}}
			highlighted={selectedMetrics[metric]}
			onClick={toggleSelection}
		>
			<SvgIcon component={METRIC_ICONS[metric]} style={{ fontSize: 48 }} />
			<h3>{METRICS_LABELS[metric]}</h3>
		</Card>
	);
}
