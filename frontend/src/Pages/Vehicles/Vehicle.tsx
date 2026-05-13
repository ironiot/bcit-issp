import classNames from "classnames/bind";
import { Card } from "@/components/Card";
import { useLocalStorage } from "@/hooks/LocalStorage";
import type { VehicleInfo } from "@/types";
import units from "@/units";
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
	const { get } = useLocalStorage();

	return (
		<Card
			className={cx("vehicle")}
			onClick={onClick}
			highlighted={vin === get("selected-vin", "")}
		>
			<h2>{model}</h2>
			<table>
				<tr>
					<th>Distance</th>
					<td>
						{distance.toFixed(1)} {units.distance}
					</td>
				</tr>
				<tr>
					<th>Last measure</th>
					{last_measure && <td>{new Date(last_measure).toLocaleString()}</td>}
				</tr>
			</table>
		</Card>
	);
}
