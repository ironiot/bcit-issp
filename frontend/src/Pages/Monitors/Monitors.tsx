import { useQuery } from "@tanstack/react-query";
import classNames from "classnames/bind";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
	CartesianGrid,
	Legend,
	Line,
	LineChart,
	ReferenceLine,
	ResponsiveContainer,
	Tooltip,
	XAxis,
	YAxis,
} from "recharts";
import { apiGet } from "@/api";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { METRICS, type Metric } from "@/metrics";
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

export function Monitors() {
	const [selectedVin, setSelectedVin] = useLocalStorage("selected-vin");
	const [selectedCycleId, setSelectedCycleId] = useState<string | null>(null);
	const [metric, setMetric] = useState<Metric>("speed");

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
		queryKey: ["samples", selectedCycleId],
		queryFn: () => {
			const fields = ["timestamp", ...METRICS].join(",");
			const q = new URLSearchParams({ fields });
			return apiGet<Sample[]>(
				`/data/samples/drive_cycle/${encodeURIComponent(selectedCycleId!)}?${q}`,
			);
		},
		enabled: !!selectedCycleId,
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

	const chartPoints = useMemo(() => {
		return samples.map((s) => {
			const timeMs = new Date(s.timestamp).getTime();
			const row: Record<string, number | null> = { timeMs };
			for (const m of METRICS) {
				const v = s[m];
				row[m] = v === undefined || v === null ? null : Number(v);
			}
			return row;
		});
	}, [samples]);

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
				<button
					type="button"
					className={cx("btnRefresh")}
					onClick={() => loadVehicles()}
				>
					Refresh
				</button>
			</header>

			{error ? (
				<p className={cx("errorBanner")} role="alert">
					{error}
				</p>
			) : null}

			{loading ? (
				<p className="muted">Loading vehicles…</p>
			) : !vehicles.length && !error ? (
				<p className="muted">No vehicles in the database yet.</p>
			) : !vehicles.length ? null : (
				<div className={cx("cards")}>
					<Card className={cx("card")} aria-label="Vehicle">
						<h2>Vehicle</h2>
						{vehicles.length > 1 ? (
							<label className={cx("field")}>
								<span>Select VIN</span>
								<select
									value={selectedVin ?? ""}
									onChange={(e) => setSelectedVin(e.target.value)}
								>
									{vehicles.map((v) => (
										<option key={v.vin} value={v.vin}>
											{v.vin}
											{v.model ? ` — ${v.model}` : ""}
										</option>
									))}
								</select>
							</label>
						) : null}
						{activeVehicle ? (
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
						) : null}
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

					<Card className={cx("card")} aria-label="Samples chart">
						<div className={cx("chartToolbar")}>
							<h2>Signals</h2>
							<label className={cx("field", "inline")}>
								<span className="sr-only">Metric</span>
								{/* TODO: dynamically generate options based on selected metrics */}
								<select
									value={metric}
									onChange={(e) => setMetric(e.target.value as Metric)}
								>
									<option value="speed">Speed</option>
									<option value="rpm">RPM</option>
									<option value="engine_load">Engine load</option>
									<option value="throttle_pos">Throttle</option>
									<option value="coolant_temp">Coolant °C</option>
									<option value="map">MAP</option>
								</select>
							</label>
						</div>
						{chartLoading ? (
							<p className="muted">Loading samples…</p>
						) : !chartPoints.length ? (
							<p className="muted">No samples for this drive cycle.</p>
						) : (
							<div className={cx("chartWrap")}>
								<ResponsiveContainer width="100%" height={320}>
									<LineChart
										data={chartPoints}
										margin={{ top: 8, right: 16, left: 0, bottom: 0 }}
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
											fontSize={11}
										/>
										<YAxis
											stroke="var(--color-chart-axis)"
											tick={{ fill: "var(--color-text-muted)" }}
											fontSize={11}
										/>
										<Tooltip
											labelFormatter={(ms) =>
												new Date(Number(ms)).toLocaleString()
											}
											contentStyle={{
												background: "var(--color-surface)",
												border: "1px solid var(--color-border-strong)",
												color: "var(--color-text)",
											}}
											labelStyle={{ color: "var(--color-text)" }}
											itemStyle={{ color: "var(--color-chart-line)" }}
										/>
										<Legend
											wrapperStyle={{ color: "var(--color-text-muted)" }}
										/>
										<Line
											type="monotone"
											dataKey={metric}
											name={metric}
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
													fontSize: 10,
													position: "top",
												}}
											/>
										))}
									</LineChart>
								</ResponsiveContainer>
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
		</div>
	);
}
