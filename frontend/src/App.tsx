import { Navigate, NavLink, Route, Routes } from "react-router-dom";
import { Errors } from "./Errors";
import { Configs } from "./Pages/Configs";
import { Monitors } from "./Pages/Monitors";

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
						Configs
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

export default function App() {
	return <Layout />;
}
