import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Config } from "./Config";
import { Errors } from "./Errors";
import { Monitors } from "./Pages/Monitors";
import { Vehicles } from "./Pages/Vehicles";

function Layout() {
	return (
		<div className="app">
			<header>
				<strong>ISSP</strong>
				<nav>
					<NavLink
						to="/"
						end
						className={({ isActive }) => (isActive ? "active" : "")}
					>
						Vehicles
					</NavLink>
					<NavLink
						to="/monitors"
						end
						className={({ isActive }) => (isActive ? "active" : "")}
					>
						Monitors
					</NavLink>
					<NavLink
						to="/errors"
						className={({ isActive }) => (isActive ? "active" : "")}
					>
						Errors
					</NavLink>
					<NavLink
						to="/config"
						className={({ isActive }) => (isActive ? "active" : "")}
					>
						Config
					</NavLink>
				</nav>
			</header>
			<main>
				<Routes>
					<Route path="/" element={<Vehicles />} />
					<Route path="/monitors" element={<Monitors />} />
					<Route path="/errors" element={<Errors />} />
					<Route path="/config" element={<Config />} />
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</main>
		</div>
	);
}

export default function App() {
	return <Layout />;
}
