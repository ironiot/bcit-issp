import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { Fragment, useCallback, useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
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
import { Modal } from "@/components/Modal";
import { VehicleSelection } from "@/components/VehicleSelection";
import { useLocalStorage } from "@/hooks/LocalStorage";
import {
	getSelectedMetrics,
	METRICS_LABELS,
	type Metric,
	UNITS,
} from "@/metrics";
import type { DriveCycle, DtcRow, Sample } from "@/types";
import { MetricSelection } from "./MetricSelection";
import styles from "./Monitors.module.css";

const cx = classNames.bind(styles);

export function Monitors() {
	const [storedVin] = useLocalStorage("selected-vin");
	const [searchParams, setSearchParams] = useSearchParams();
	const urlVin = searchParams.get("vin");
	const urlDriveCycleId = searchParams.get("drive_id");

	const selectedVin = urlVin ?? storedVin;
	const [metricsSelection] = useLocalStorage("metrics-selection");

	const [selectedCycleId, setSelectedCycleId] = useState(urlDriveCycleId);
	const selectDriveCycle = useCallback(
		(id: string) => {
			setSelectedCycleId(id);
			if (urlVin) {
				const newParams = new URLSearchParams();
				newParams.set("vin", urlVin);
				setSearchParams(newParams, { replace: true });
			} else {
				setSearchParams({}, { replace: true });
			}
		},
		[setSearchParams, urlVin],
	);

	const [highlightedMetric, highlightMetric] = useState<Metric>();

	const selectedMetrics = useMemo(
		() => getSelectedMetrics(metricsSelection),
		[metricsSelection],
	);
	const selectedMetricsStr = selectedMetrics.join(",");

	const {
		data: driveCycles = [],
		refetch: refetchDriveCycles,
		error: driveCyclesFetchError,
	} = useQuery({
		queryKey: ["driveCycles", selectedVin],
		queryFn: () =>
			apiGet<DriveCycle[]>(
				`/data/drives_cycles/${encodeURIComponent(selectedVin!)}`,
			),
		enabled: !!selectedVin,
	});

	useEffect(() => {
		// auto-select the first drive cycle if none is selected yet
		if (
			driveCycles.length &&
			(!selectedCycleId || !driveCycles.some((c) => c.id === selectedCycleId))
		) {
			selectDriveCycle(driveCycles[0].id);
		}
	}, [driveCycles, selectDriveCycle, selectedCycleId]);

	const selectedDriveCycle = useMemo(
		() => driveCycles.find((c) => c.id === selectedCycleId) ?? null,
		[driveCycles, selectedCycleId],
	);

	const {
		data: samples = [],
		isLoading: chartLoading,
		refetch: refetchSamples,
		error: samplesFetchError,
	} = useQuery({
		queryKey: ["samples", selectedCycleId, selectedMetricsStr],
		queryFn: () => {
			const q = new URLSearchParams({ fields: selectedMetricsStr });
			return apiGet<Sample[]>(
				`/data/samples/drive_cycle/${encodeURIComponent(selectedCycleId!)}?${q}`,
			);
		},
		enabled: !!selectedCycleId && selectedMetrics.length > 0,
	});

	const {
		data: dtcs = [],
		refetch: refetchDtcs,
		error: dtcsFetchError,
	} = useQuery({
		queryKey: ["vinDtcs", selectedVin],
		queryFn: () =>
			apiGet<DtcRow[]>(`/data/dtcs/${encodeURIComponent(selectedVin!)}`),
		enabled: !!selectedVin,
	});

	const errorData =
		driveCyclesFetchError || samplesFetchError || dtcsFetchError;
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
		if (!selectedDriveCycle) {
			return {};
		}

		const start = new Date(selectedDriveCycle.start_time).getTime();
		const end = selectedDriveCycle.end_time
			? new Date(selectedDriveCycle.end_time).getTime()
			: Number.POSITIVE_INFINITY;

		const map: Record<number, DtcRow[]> = {};
		dtcs
			.filter((d) => {
				const t = new Date(d.timestamp).getTime();
				return t >= start && t <= end;
			})
			.forEach((d) => {
				const t = Math.round(new Date(d.timestamp).getTime() / 1000) * 1000;
				map[t] = [...(map[t] ?? []), d];
			});
		return map;
	}, [selectedDriveCycle, dtcs]);

	const [isMetricsFilterOpen, setOpenMetricsFilter] = useState(false);

	return (
		<div className={cx("monitors")}>
			<header className={cx("monitorsHeader")}>
				<h1>Monitors</h1>
				<Button
					onClick={() => {
						refetchDriveCycles();
						refetchSamples();
						refetchDtcs();
					}}
					text="Refresh"
				/>
			</header>

			{error && (
				<p className={cx("errorBanner")} role="alert">
					{error}
				</p>
			)}

			<div className={cx("cards")}>
				<VehicleSelection className={cx("card")} />

				<Card className={cx("card")} aria-label="Drive cycle">
					<h2>Drive cycle</h2>
					{!driveCycles.length ? (
						<p className="muted">No drive cycles for this vehicle.</p>
					) : (
						<label className={cx("field")}>
							<span>Trip</span>
							<select
								value={selectedCycleId ?? ""}
								onChange={(e) => selectDriveCycle(e.target.value)}
							>
								{driveCycles.map((dc) => (
									<option key={dc.id} value={dc.id}>
										{formatTime(dc.start_time)}
										{dc.end_time ? "" : " (active)"}
										{cycleInError(dc, dtcs) ? " ⚠" : ""}
									</option>
								))}
							</select>
						</label>
					)}
				</Card>

				{selectedCycleId && (
					<Card className={cx("card")} aria-label="Signals">
						<div className={cx("chartToolbar")}>
							<h2>Signals</h2>
							<Button
								onClick={() => setOpenMetricsFilter(true)}
								text="Select metrics"
							/>
						</div>
						<MetricSelection
							open={isMetricsFilterOpen}
							onClose={() => setOpenMetricsFilter(false)}
						/>
						{isMetricsFilterOpen ? null : chartLoading ? (
							<p className="muted">Loading samples…</p>
						) : !selectedMetrics.length ? (
							<p className="muted">No metrics selected.</p>
						) : !chartPoints.length ? (
							<p className="muted">No samples for this drive cycle.</p>
						) : (
							<div className={cx("chartGrid")}>
								{selectedMetrics.map((metric) => (
									<SignalChart
										key={metric}
										metric={metric}
										data={chartPoints}
										dtcTimes={Object.keys(cycleDtcs).map(Number)}
										onClick={() => highlightMetric(metric)}
									/>
								))}
								<Modal
									open={highlightedMetric !== undefined}
									onClose={() => highlightMetric(undefined)}
								>
									<Card className={cx("chartModal")}>
										{highlightedMetric && (
											<SignalChart
												metric={highlightedMetric}
												data={chartPoints}
												dtcTimes={Object.keys(cycleDtcs).map(Number)}
												height={400}
											/>
										)}
									</Card>
								</Modal>
							</div>
						)}
						{Object.keys(cycleDtcs).length > 0 && (
							<>
								<h4 className={cx("dtcHeader")}>Errors:</h4>
								<ul className={cx("dtcLinks")}>
									{Object.keys(cycleDtcs).map((epochMs) => {
										const time = new Date(Number(epochMs)).toLocaleString();
										return (
											<li key={epochMs}>
												<span className={cx("dtcTime")}>{time}</span>
												{cycleDtcs[Number(epochMs)].map(
													({ id, code }, index, array) => (
														<Fragment key={id}>
															<Link
																to={
																	"/errors" +
																	`?vin=${encodeURIComponent(selectedVin ?? "")}` +
																	`&dtc=${encodeURIComponent(id)}`
																}
															>
																{code}
															</Link>
															{index < array.length - 1 ? ", " : ""}
														</Fragment>
													),
												)}
											</li>
										);
									})}
								</ul>
							</>
						)}
					</Card>
				)}
			</div>
		</div>
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
	dtcTimes: number[];
	height?: number;
	onClick?: () => void;
};

function SignalChart({
	metric,
	data,
	dtcTimes,
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
						margin={{
							top: dtcTimes.length ? 16 : 0,
							right: 12,
							left: 0,
							bottom: 0,
						}}
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
						{dtcTimes.map((time) => (
							<ReferenceLine
								key={time}
								x={Number(time)}
								stroke="var(--color-chart-dtc)"
								strokeWidth={2}
								strokeDasharray={8}
								label={{
									value: "⚠",
									fill: "var(--color-chart-dtc)",
									fontSize: 14,
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
