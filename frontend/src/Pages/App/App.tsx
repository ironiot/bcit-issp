import classNames from "classnames/bind";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { useLocalStorage } from "@/hooks/LocalStorage";
import { Errors } from "../../Errors";
import { Configs } from "../Configs";
import { Monitors } from "../Monitors";
import styles from "./App.module.css";

const cx = classNames.bind(styles);

export function App() {
	const [selectedVin] = useLocalStorage("selected-vin");
	const [metricsSelection] = useLocalStorage("metrics-selection");

	const isConfigMissing =
		!selectedVin ||
		!metricsSelection ||
		!Object.values(metricsSelection).some((v) => v);

	return (
		<div className={cx("app")}>
			<header>
				<strong>ISSP</strong>
				<nav>
					<NavLink to="/" end className={({ isActive }) => cx({ isActive })}>
						Configs
					</NavLink>
					{!isConfigMissing && (
						<>
							<NavLink
								to="/monitors"
								end
								className={({ isActive }) => cx({ isActive })}
							>
								Monitors
							</NavLink>
							<NavLink
								to="/errors"
								className={({ isActive }) => cx({ isActive })}
							>
								Errors
							</NavLink>
						</>
					)}
				</nav>
			</header>
			<main>
				<Routes>
					<Route path="/" element={<Configs />} />
					<Route path="/monitors" element={<Monitors />} />
					<Route path="/errors" element={<Errors />} />
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</div>
	);
}
