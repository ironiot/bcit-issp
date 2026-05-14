import { Grid } from "@/components/Grid";
import { METRICS } from "@/metrics";
import { MetricCard } from "./MetricCard";

const gridData = METRICS.map((metric) => ({ metric, key: metric }));

export function MetricsSelection() {
	return <Grid data={gridData} Item={MetricCard} />;
}
