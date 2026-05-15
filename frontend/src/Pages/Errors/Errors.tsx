import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiGet } from "@/api";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { DtcRow, SampleData, VehicleInfo } from "@/types";
import styles from "./Errors.module.css";
import { UNITS } from "@/metrics";

export function Errors() {

  // all the state I need
  const [vehicles, setVehicles] = useState<VehicleInfo[]>([]);
  const [storedVin, setStoredVin] = useLocalStorage("selected-vin");
  const [selectedVin, setSelectedVin] = useState("");
  const [dtcs, setDtcs] = useState<DtcRow[]>([]);
  const [selectedId, setSelectedId] = useState<number | "">("");

  //vehicle selection upon load, just gotten through localstorage
  useEffect(() => {
   
    if (storedVin) {
      setSelectedVin(storedVin);
    }
  }, [storedVin, setStoredVin]);

  //load vehicles on startup
  useEffect(() => {
    let mounted = true;

    apiGet<VehicleInfo[]>("/data/vehicles")
      .then((data) => {
        if (!mounted) return;

        const safeVehicles = Array.isArray(data) ? data : [];
        console.log("Vehicles loaded:", safeVehicles.map((v) => v.vin));

        setVehicles(safeVehicles);

        if (!selectedVin && safeVehicles.length > 0) {
          console.log("Auto-selecting VIN:", safeVehicles[0].vin);
          setSelectedVin(safeVehicles[0].vin);
        }
      })
      .catch(() => {
        if (!mounted) return;
        console.log("Vehicles load failed");
        setVehicles([]);
      });

    return () => {
      mounted = false;
    };
  }, [selectedVin]);

  //load dtcs using vin
  useEffect(() => {
    if (!selectedVin) {
      console.log("No VIN selected, skipping DTC fetch");
      setDtcs([]);
      setSelectedId("");
      return;
    }

    let mounted = true;
    setDtcs([]);
    setSelectedId("");

    apiGet<DtcRow[]>(`/data/dtcs/${encodeURIComponent(selectedVin)}`)
      .then((data) => {
        if (!mounted) return;
        const safeDtcs = Array.isArray(data) ? data : [];
        console.log("DTCs loaded:", safeDtcs.length);
        setDtcs(safeDtcs);
      })
      .catch((err) => {
        if (!mounted) return;
        console.log("DTC load failed for VIN:", selectedVin, err);
        setDtcs([]);
      });

    return () => {
      mounted = false;
    };
  }, [selectedVin]);

  //selected the first active dtc
  useEffect(() => {
    if (selectedId !== "") return;

    const active = dtcs.find((d) => d.cleared_at === null);
    if (active) setSelectedId(active.id);
  }, [dtcs, selectedId]);

  const selected = useMemo(
    () => dtcs.find((d) => d.id === selectedId) ?? null,
    [dtcs, selectedId]
  );


  return (
    <div className={styles.errors}>
      <header className={styles.errorsHeader}>
        <h1>Errors</h1>
      </header>

      <div className={styles.columns}>
        <Card className={styles.leftCol} aria-label="Error details">
          {!selected ? (
            <p className="muted">No errors</p>
          ) : (
            <>
              <h2>
                {selected.code}: {selected.description}
              </h2>

              <dl className={styles.detailGrid}>
                <div>
                  <dt>VIN</dt>
                  <dd>{selected.vin}</dd>
                </div>
                <div>
                  <dt>Timestamp</dt>
                  <dd>{new Date(selected.timestamp).toLocaleString()}</dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{selected.cleared_at ? "Cleared" : "Active"}</dd>
                </div>
              </dl>

              <h3>Freeze frame</h3>
              {selected.freeze_frame ? (
                <table className={styles.freezeTable}>
                  <thead>
                    <tr>
                      <th>Metric</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(selected.freeze_frame as SampleData).map(
                      ([metric, value]) => (
                        <tr key={metric}>
                          {value === null || metric === "id" || metric === "dtc_id" ? (
                            <>     </>
                          ) : (
                            <><td>{metric}</td><td>{`${String(value)}${UNITS[metric as keyof typeof UNITS]}`}</td></>
                          )}
                        </tr>
                      )
                    )}
                  </tbody>
                </table>
              ) : (
                <p className="muted">No freeze frame data</p>
              )}
              {/* Definitely a TODO, not sure if link to monitors even fully works */}
              <p className={styles.monitorLink}>
                <Link
                  to={`/monitors?vin=${encodeURIComponent(
                    selected.vin
                  )}&ts=${encodeURIComponent(selected.timestamp)}`}
                  onClick={() => setStoredVin(selected.vin)}
                >
                  Open in Monitors
                </Link>
              </p>
            </>
          )}
        </Card>

     
        <div className={styles.rightCol}>
          <Card className={styles.vehicleCard} aria-label="Vehicle">
            <label className={styles.field}>
              <span>Vehicle</span>
              <select
                value={selectedVin}
                onChange={(e) => {
                  setSelectedVin(e.target.value);
                  setStoredVin(e.target.value);
                }}
              >
                <option value="">-- select vehicle --</option>
                {vehicles.map((v) => (
                  <option key={v.vin} value={v.vin}>
                   
                    {v.model ? ` ${v.model}` : ""}
                  </option>
                ))}
              </select>
            </label>
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
                        selectedId === d.id ? styles.selected : ""
                      }`}
                      onClick={() => setSelectedId(d.id)}
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
    </div>
  );
}
