import { SvgIcon } from "@mui/material";
import classNames from "classnames/bind";
import { useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { METRIC_ICONS, METRICS_LABELS, type Metric } from "@/metrics";
import styles from "./Monitors.module.css";

const cx = classNames.bind(styles);

type Props = { metric: Metric };
export function MetricCard({ metric }: Props) {
	const [metricsSelection, setMetricsSelection] =
		useLocalStorage("metrics-selection");

	const [highlighted, setHighlighted] = useState(metricsSelection?.[metric]);
	useEffect(() => {
		if (metricsSelection) {
			setHighlighted(metricsSelection[metric]);
		}
	}, [metricsSelection, metric]);

	const toggleSelection = () => {
		if (metricsSelection) {
			setMetricsSelection({
				...metricsSelection,
				[metric]: !metricsSelection[metric],
			});
		}
	};

	return (
		<Card
			className={cx("metric-card")}
			highlighted={highlighted}
			onClick={toggleSelection}
		>
			<SvgIcon component={METRIC_ICONS[metric]} style={{ fontSize: 32 }} />
			<h4>{METRICS_LABELS[metric]}</h4>
		</Card>
	);
}
