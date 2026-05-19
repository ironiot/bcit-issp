import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { apiGet } from "@/api";
import { Button } from "@/components/Button";
import { Card } from "@/components/Card";
import { VehicleSelection } from "@/components/VehicleSelection";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { METRICS_LABELS, UNITS } from "@/metrics";
import type { DtcRow, SampleData } from "@/types";
import styles from "./Errors.module.css";

export function Errors() {
	const [storedVin] = useLocalStorage("selected-vin");
	const [searchParams, setSearchParams] = useSearchParams();
	const urlVin = searchParams.get("vin");

	const selectedVin = urlVin ?? storedVin;

	const { data: dtcs = [], refetch: refetchDtcs } = useQuery({
		queryKey: ["dtcs", selectedVin],
		queryFn: () =>
			apiGet<DtcRow[]>(`/data/dtcs/${encodeURIComponent(selectedVin ?? "")}`),
		enabled: !!selectedVin,
	});

	const urlDtcId = searchParams.get("dtc");
	const [selectedDtc, setSelectedDtc] = useState<DtcRow | undefined>();

	useEffect(() => {
		// select the DTC from the URL if it exists
		if (urlDtcId) {
			const dtcFromUrl = dtcs.find((d) => String(d.id) === urlDtcId);
			if (dtcFromUrl) {
				setSelectedDtc(dtcFromUrl);
				return;
			}
		}
		// otherwise select the first active DTC by default
		setSelectedDtc(
			(current) => current || dtcs.find((d) => d.cleared_at === null),
		);
	}, [dtcs, urlDtcId]);

	const selectDtc = (dtc: DtcRow) => {
		setSelectedDtc(dtc);
		if (urlVin) {
			const newParams = new URLSearchParams();
			newParams.set("vin", urlVin);
			setSearchParams(newParams, { replace: true });
		} else {
			setSearchParams({}, { replace: true });
		}
	};

	return (
		<div className={styles.errors}>
			<header className={styles.errorsHeader}>
				<h1>Errors</h1>
				<Button onClick={() => refetchDtcs()} text="Refresh" />
			</header>

			<VehicleSelection className={styles.VehicleSelection} />

			<div className={styles.columns}>
				<Card className={styles.leftCol} aria-label="Error details">
					{!selectedDtc ? (
						<p className="muted">No errors</p>
					) : (
						<>
							<h2>
								{selectedDtc.code}: {selectedDtc.description}
							</h2>

							<dl className={styles.detailGrid}>
								<div>
									<dt>Timestamp</dt>
									<dd>{new Date(selectedDtc.timestamp).toLocaleString()}</dd>
								</div>
								<div>
									<dt>Status</dt>
									<dd>{selectedDtc.cleared_at ? "Cleared" : "Active"}</dd>
								</div>
							</dl>

							<h3>Freeze frame</h3>
							{selectedDtc.freeze_frame ? (
								<table className={styles.freezeTable}>
									<thead>
										<tr>
											<th>Metric</th>
											<th>Value</th>
										</tr>
									</thead>
									<tbody>
										{Object.entries(selectedDtc.freeze_frame as SampleData).map(
											([metric, value]) => (
												<tr key={metric}>
													{value === null ||
													metric === "id" ||
													metric === "dtc_id" ? (
														<> </>
													) : (
														<>
															<td>{METRICS_LABELS[metric] ?? metric}</td>
															<td>{`${String(value)}${UNITS[metric] ?? ""}`}</td>
														</>
													)}
												</tr>
											),
										)}
									</tbody>
								</table>
							) : (
								<p className="muted">No freeze frame data</p>
							)}
							<p className={styles.monitorLink}>
								<Link
									to={
										"/monitors" +
										`?vin=${encodeURIComponent(selectedVin ?? "")}` +
										`&dtc_ts=${encodeURIComponent(selectedDtc.timestamp)}`
									}
								>
									Open in Monitors
								</Link>
							</p>
						</>
					)}
				</Card>

				<Card className={styles.listCard} aria-label="Historical errors">
					{!dtcs.length ? (
						<p className="muted">No historical errors</p>
					) : (
						<ul className={styles.errorList}>
							{dtcs.map((d) => (
								<li key={d.id}>
									<button
										type="button"
										className={`${styles.errorItem} ${
											selectedDtc?.id === d.id ? styles.selected : ""
										}`}
										onClick={() => selectDtc(d)}
										title={d.description ?? ""}
									>
										<strong>
											{d.code}
											{d.cleared_at === null ? " (active)" : ""}
										</strong>
										<span>{new Date(d.timestamp).toLocaleString()}</span>
									</button>
								</li>
							))}
						</ul>
					)}
				</Card>
			</div>
		</div>
	);
}
