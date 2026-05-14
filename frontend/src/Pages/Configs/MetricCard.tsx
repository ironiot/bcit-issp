import { SvgIcon } from "@mui/material";
import classNames from "classnames/bind";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import {
	DEFAULT_ENABLED_METRICS,
	METRIC_ICONS,
	METRICS,
	METRICS_LABELS,
	type Metric,
} from "@/metrics";
import styles from "./Configs.module.css";

const cx = classNames.bind(styles);

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
			className={cx("metric-card")}
			highlighted={selectedMetrics[metric]}
			onClick={toggleSelection}
		>
			<SvgIcon component={METRIC_ICONS[metric]} style={{ fontSize: 32 }} />
			<h4>{METRICS_LABELS[metric]}</h4>
		</Card>
	);
}
