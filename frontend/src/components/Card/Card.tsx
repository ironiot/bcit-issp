import classNames from "classnames/bind";
import type { CSSProperties, ReactNode } from "react";
import styles from "./Card.module.css";

const cx = classNames.bind(styles);

type CardProps = {
	highlighted?: boolean;
	className?: string;
	children: ReactNode;
	style?: CSSProperties;
	onClick?: () => void;
};

export function Card({ highlighted, onClick, className, ...rest }: CardProps) {
	const interactive = onClick != null;
	return (
		<div
			className={cx("card", { highlighted, interactive }, className)}
			onClick={onClick}
			{...rest}
		/>
	);
}
