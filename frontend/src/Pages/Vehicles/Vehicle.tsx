import classNames from "classnames/bind";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { UNITS } from "@/metrics";
import type { VehicleInfo } from "@/types";
import styles from "./Vehicles.module.css";

const cx = classNames.bind(styles);

type VehicleProps = {
	data: VehicleInfo;
	onClick?: () => void;
};

export function Vehicle({
	data: { vin, model, distance, last_measure },
	onClick,
}: VehicleProps) {
	const [selectedVin] = useLocalStorage("selected-vin");

	return (
		<Card
			className={cx("vehicle")}
			onClick={onClick}
			highlighted={vin === selectedVin}
		>
			<h2>{model}</h2>
			<table>
				<tbody>
					<tr>
						<th>Distance</th>
						<td>
							{distance.toFixed(1)} {UNITS.distance}
						</td>
					</tr>
					<tr>
						<th>Last measure</th>
						{last_measure && <td>{new Date(last_measure).toLocaleString()}</td>}
					</tr>
				</tbody>
			</table>
		</Card>
	);
}
