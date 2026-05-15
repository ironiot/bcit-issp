import { SvgIcon } from "@mui/material";
import classNames from "classnames/bind";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import {
	DEFAULT_METRICS,
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
		metricsSelection = Object.fromEntries(
			METRICS.map((m) => [m, DEFAULT_METRICS.has(m)]),
		) as Record<Metric, boolean>,
		setMetricsSelection,
	] = useLocalStorage("metrics-selection");

	const toggleSelection = () =>
		setMetricsSelection({
			...metricsSelection,
			[metric]: !metricsSelection[metric],
		});

	return (
		<Card
			className={cx("metric-card")}
			highlighted={metricsSelection[metric]}
			onClick={toggleSelection}
		>
			<SvgIcon component={METRIC_ICONS[metric]} style={{ fontSize: 32 }} />
			<h4>{METRICS_LABELS[metric]}</h4>
		</Card>
	);
}
