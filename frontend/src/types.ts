

export interface Vehicle {
  vin: string;
  calibration_id: string | null;
  cvn: string | null;
  ecu_name: string | null;
}

export interface DashboardData {
  vehicles: Vehicle[];
}
