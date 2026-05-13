/**
 * Vehicle row plus aggregates from `GET /data/vehicles`.
 */
export interface VehicleWithStats {
	vin: string;
	calibration_id: string | null;
	cvn: string | null;
	model: string | null;
	body_type: string | null;
	fuel_type: string | null;
	transmission: string | null;
	drive_type: string | null;
	drive_cycles_count: number;
	total_dtcs_count: number;
	active_dtcs: string[];
	first_measure: string | null;
	last_measure: string | null;
	distance: number;
}

export interface DriveCycle {
	id: string;
	vin: string;
	start_time: string;
	end_time: string | null;
	distance: number | null;
}

export interface DtcRow {
	id: number;
	vin: string;
	code: string;
	description: string | null;
	timestamp: string;
	cleared_at: string | null;
	freeze_frame: Record<string, unknown> | null;
}

// TODO: config page to select these
export const CHART_METRICS = [
	"rpm",
	"speed",
	"engine_load",
	"throttle_pos",
	"coolant_temp",
	"map",
] as const;

export type SampleRow = {
	timestamp: string;
} & Partial<Record<(typeof CHART_METRICS)[number], number | null>>;
