import classNames from "classnames/bind";
import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Configs } from "../Configs";
import { ConfigValidator, useIsConfigMissing } from "../ConfigValidator";
import { Errors } from "../Errors";
import { Monitors } from "../Monitors";
import styles from "./App.module.css";

const cx = classNames.bind(styles);

export function App() {
	const isConfigMissing = useIsConfigMissing();

	return (
		<div className={cx("app")}>
			<header>
				<strong>ISSP</strong>
				<nav>
					{!isConfigMissing && (
						<>
							<NavLink
								to="/"
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
					<NavLink
						to="/configs"
						end
						className={({ isActive }) => cx({ isActive })}
					>
						Configs
					</NavLink>
				</nav>
			</header>
			<main>
				<Routes>
					<Route path="/" element={<ConfigValidator Renderer={Monitors} />} />
					<Route
						path="/errors"
						element={<ConfigValidator Renderer={Errors} />}
					/>
					<Route path="/configs" element={<Configs />} />
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</div>
	);
}
