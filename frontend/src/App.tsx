import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Config } from "./Config";
import { Dashboard } from "./Dashboard";

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
						Dashboard
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
					<Route path="/" element={<Dashboard />} />
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
