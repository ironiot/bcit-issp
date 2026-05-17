import { Modal } from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
	CartesianGrid,
	Line,
	LineChart,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { apiGet } from "@/api";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import {
	getSelectedMetrics,
	METRICS_LABELS,
	type Metric,
	UNITS,
} from "@/metrics";
import type { DriveCycle, DtcRow, Sample, VehicleInfo } from "@/types";
import styles from "./Monitors.module.css";

const cx = classNames.bind(styles);

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

function cycleInError(dc: DriveCycle, dtcs: DtcRow[]): boolean {
	const start = new Date(dc.start_time).getTime();
	const end = dc.end_time
		? new Date(dc.end_time).getTime()
		: Number.POSITIVE_INFINITY;
	return dtcs.some((d) => {
		const t = new Date(d.timestamp).getTime();
		return t >= start && t <= end;
	});
}

type ChartPoint = { timeMs: number } & Record<string, number | null>;

type SignalChartProps = {
	metric: Metric;
	data: ChartPoint[];
	cycleDtcs: DtcRow[];
	height?: number;
	onClick?: () => void;
};

function SignalChart({
	metric,
	data,
	cycleDtcs,
	height = 220,
	onClick,
}: SignalChartProps) {
	const unit = UNITS[metric];

	return (
		<article
			className={cx("signalChart")}
			aria-label={METRICS_LABELS[metric]}
			onClick={onClick}
		>
			<h3 className={cx("signalChartTitle")}>{METRICS_LABELS[metric]}</h3>
			<div className={cx("chartWrap")}>
				<ResponsiveContainer width="100%" height={height}>
					<LineChart
						data={data}
						margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
					>
						<CartesianGrid
							stroke="var(--color-chart-grid)"
							strokeDasharray="3 3"
						/>
						<XAxis
							type="number"
							dataKey="timeMs"
							domain={["dataMin", "dataMax"]}
							tickFormatter={(ms: number) =>
								new Date(ms).toLocaleTimeString(undefined, {
									hour: "2-digit",
									minute: "2-digit",
									second: "2-digit",
								})
							}
							stroke="var(--color-chart-axis)"
							tick={{ fill: "var(--color-text-muted)" }}
							fontSize={10}
						/>
						<YAxis
							stroke="var(--color-chart-axis)"
							tick={{ fill: "var(--color-text-muted)" }}
							fontSize={10}
							width={48}
						/>
						<Tooltip
							labelFormatter={(ms) => new Date(Number(ms)).toLocaleString()}
							formatter={(value) => [
								value != null ? `${value}${unit}` : "—",
								METRICS_LABELS[metric],
							]}
							contentStyle={{
								background: "var(--color-surface)",
								border: "1px solid var(--color-border-strong)",
								color: "var(--color-text)",
							}}
							labelStyle={{ color: "var(--color-text)" }}
						/>
						<Line
							type="monotone"
							dataKey={metric}
							name={METRICS_LABELS[metric]}
							stroke="var(--color-accent)"
							dot={false}
							strokeWidth={2}
							connectNulls
						/>
						{cycleDtcs.map((d) => (
							<ReferenceLine
								key={d.id}
								x={new Date(d.timestamp).getTime()}
								stroke="var(--color-chart-dtc)"
								strokeWidth={2}
								strokeOpacity={0.95}
								label={{
									value: d.code,
									fill: "var(--color-chart-dtc)",
									fontSize: 9,
									position: "top",
								}}
							/>
						))}
					</LineChart>
				</ResponsiveContainer>
			</div>
		</article>
	);
}

export function Monitors() {
	const [selectedVin] = useLocalStorage("selected-vin");
	const [metricsSelection] = useLocalStorage("metrics-selection");
	const [selectedCycleId, setSelectedCycleId] = useState<string | null>(null);

	const selectedMetrics = useMemo(
		() => getSelectedMetrics(metricsSelection),
		[metricsSelection],
	);

	const selectedMetricsKey = selectedMetrics.join(",");

	const [highlightedMetric, highlightMetric] = useState<Metric>();

	const {
		data: vehicles = [],
		isLoading: loading,
		error: vehiclesError,
		refetch: loadVehicles,
	} = useQuery({
		queryKey: ["vehicles"],
		queryFn: () => apiGet<VehicleInfo[]>("/data/vehicles"),
	});

	const { data: driveCycles = [], error: driveCyclesError } = useQuery({
		queryKey: ["driveCycles", selectedVin],
		queryFn: () =>
			apiGet<DriveCycle[]>(
				`/data/drives_cycles/${encodeURIComponent(selectedVin!)}`,
			),
		enabled: !!selectedVin,
	});

	useEffect(() => {
		if (!driveCycles.length) {
			setSelectedCycleId(null);
			return;
		}
		if (
			!selectedCycleId ||
			!driveCycles.some((c) => c.id === selectedCycleId)
		) {
			setSelectedCycleId(driveCycles[0].id);
		}
	}, [driveCycles, selectedCycleId]);

	const selectedCycle = useMemo(
		() => driveCycles.find((c) => c.id === selectedCycleId) ?? null,
		[driveCycles, selectedCycleId],
	);

	const {
		data: samples = [],
		isLoading: chartLoading,
		error: samplesError,
	} = useQuery({
		queryKey: ["samples", selectedCycleId, selectedMetricsKey],
		queryFn: () => {
			const fields = ["timestamp", ...selectedMetrics].join(",");
			const q = new URLSearchParams({ fields });
			return apiGet<Sample[]>(
				`/data/samples/drive_cycle/${encodeURIComponent(selectedCycleId!)}?${q}`,
			);
		},
		enabled: !!selectedCycleId && selectedMetrics.length > 0,
	});

	const { data: vinDtcs = [], error: vinDtcsError } = useQuery({
		queryKey: ["vinDtcs", selectedVin],
		queryFn: () =>
			apiGet<DtcRow[]>(`/data/dtcs/${encodeURIComponent(selectedVin!)}`),
		enabled: !!selectedVin,
	});

	const errorData =
		vehiclesError || driveCyclesError || samplesError || vinDtcsError;
	const error =
		errorData instanceof Error
			? errorData.message
			: errorData
				? String(errorData)
				: null;

	const chartPoints = useMemo((): ChartPoint[] => {
		return samples.map((s) => {
			const timeMs = new Date(s.timestamp).getTime();
			const row: ChartPoint = { timeMs };
			for (const m of selectedMetrics) {
				const v = s[m];
				row[m] = v === undefined || v === null ? null : Number(v);
			}
			return row;
		});
	}, [samples, selectedMetrics]);

	const cycleDtcs = useMemo(() => {
		if (!selectedCycle) return [];
		const start = new Date(selectedCycle.start_time).getTime();
		const end = selectedCycle.end_time
			? new Date(selectedCycle.end_time).getTime()
			: Number.POSITIVE_INFINITY;
		return vinDtcs.filter((d) => {
			const t = new Date(d.timestamp).getTime();
			return t >= start && t <= end;
		});
	}, [selectedCycle, vinDtcs]);

	const activeVehicle = vehicles.find((v) => v.vin === selectedVin);

	return (
		<div className={cx("monitors")}>
			<header className={cx("monitorsHeader")}>
				<h1>Monitors</h1>
				<Button onClick={loadVehicles} text="Refresh" />
			</header>

			{error ? (
				<p className={cx("errorBanner")} role="alert">
					{error}
				</p>
			) : null}

			{loading ? (
				<p className="muted">Loading vehicles…</p>
			) : (
				<div className={cx("cards")}>
					<Card className={cx("card")} aria-label="Vehicle">
						<h2>Vehicle</h2>
						{activeVehicle && (
							<dl className={cx("vehicleGrid")}>
								<div>
									<dt>VIN</dt>
									<dd>{activeVehicle.vin}</dd>
								</div>
								<div>
									<dt>Model</dt>
									<dd>{activeVehicle.model ?? "—"}</dd>
								</div>
								<div>
									<dt>Body</dt>
									<dd>{activeVehicle.body_type ?? "—"}</dd>
								</div>
								<div>
									<dt>Fuel</dt>
									<dd>{activeVehicle.fuel_type ?? "—"}</dd>
								</div>
								<div>
									<dt>Drive cycles</dt>
									<dd>{activeVehicle.drive_cycles_count}</dd>
								</div>
								<div>
									<dt>Distance (stored)</dt>
									<dd>
										{typeof activeVehicle.distance === "number"
											? `${activeVehicle.distance.toFixed(1)} km`
											: "—"}
									</dd>
								</div>
								<div>
									<dt>Active DTCs</dt>
									<dd>
										{activeVehicle.active_dtcs?.filter(Boolean).length
											? activeVehicle.active_dtcs.filter(Boolean).join(", ")
											: "None"}
									</dd>
								</div>
								<div>
									<dt>Last sample</dt>
									<dd>
										{activeVehicle.last_measure
											? formatTime(activeVehicle.last_measure)
											: "—"}
									</dd>
								</div>
							</dl>
						)}
					</Card>

					<Card className={cx("card")} aria-label="Drive cycle">
						<h2>Drive cycle</h2>
						{!driveCycles.length ? (
							<p className="muted">No drive cycles for this vehicle.</p>
						) : (
							<label className={cx("field")}>
								<span>Trip</span>
								<select
									value={selectedCycleId ?? ""}
									onChange={(e) => setSelectedCycleId(e.target.value)}
								>
									{driveCycles.map((dc) => (
										<option key={dc.id} value={dc.id}>
											{formatTime(dc.start_time)}
											{dc.end_time ? "" : " (active)"}
											{cycleInError(dc, vinDtcs) ? " ⚠" : ""}
										</option>
									))}
								</select>
							</label>
						)}
					</Card>

					<Card className={cx("card")} aria-label="Signals">
						<div className={cx("chartToolbar")}>
							<h2>Signals</h2>
							<span className="muted">
								{selectedMetrics.length} metric
								{selectedMetrics.length === 1 ? "" : "s"} from Configs
							</span>
						</div>
						{chartLoading ? (
							<p className="muted">Loading samples…</p>
						) : !selectedMetrics.length ? (
							<p className="muted">
								No metrics selected. Choose metrics on the Configs page.
							</p>
						) : !chartPoints.length ? (
							<p className="muted">No samples for this drive cycle.</p>
						) : (
							<div className={cx("chartGrid")}>
								{selectedMetrics.map((metric) => (
									<SignalChart
										key={metric}
										metric={metric}
										data={chartPoints}
										cycleDtcs={cycleDtcs}
										onClick={() => highlightMetric(metric)}
									/>
								))}
							</div>
						)}
						{cycleDtcs.length > 0 ? (
							<ul className={`${cx("dtcLinks")} muted`}>
								{cycleDtcs.map((d) => (
									<li key={d.id}>
										<Link to={`/errors?dtc=${d.id}`}>
											{d.code} at {formatTime(d.timestamp)}
										</Link>
									</li>
								))}
							</ul>
						) : null}
					</Card>
				</div>
			)}
			<Modal
				open={highlightedMetric !== undefined}
				onClose={() => highlightMetric(undefined)}
			>
				<Card className={cx("modalContent")}>
					{highlightedMetric && (
						<SignalChart
							metric={highlightedMetric}
							data={chartPoints}
							cycleDtcs={cycleDtcs}
							height={400}
						/>
					)}
				</Card>
			</Modal>
		</div>
	);
}
