import classNames from "classnames/bind";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Errors } from "../Errors";
import { Monitors } from "../Monitors";
import styles from "./App.module.css";

const cx = classNames.bind(styles);

export function App() {
	return (
		<div className={cx("app")}>
			<header>
				<strong>ISSP</strong>
				<nav>
					<NavLink to="/" end className={({ isActive }) => cx({ isActive })}>
						Monitors
					</NavLink>
					<NavLink to="/errors" className={({ isActive }) => cx({ isActive })}>
						Errors
					</NavLink>
				</nav>
			</header>
			<main>
				<Routes>
					<Route path="/" element={<Monitors />} />
					<Route path="/errors" element={<Errors />} />
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</div>
	);
}
