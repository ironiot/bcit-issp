import classNames from "classnames/bind";
import { useRef } from "react";
import styles from "./Grid.module.css";

const cx = classNames.bind(styles);

type GridProps<T> = {
	data: Array<T & { key: string }>;
	Item: (props: { data: T; onClick?: () => void }) => JSX.Element | null;
	itemWidth: number;
	onClickItem?: (item: T) => void;
	className?: string;
};

export function Grid<T>({
	data,
	Item,
	onClickItem,
	itemWidth,
	className,
}: GridProps<T>) {
	const containerRef = useRef<HTMLDivElement>(null);
	const firstItemRef = useRef<HTMLDivElement>(null);

	return (
		<div
			ref={containerRef}
			style={{ ["--item-width" as string]: `${itemWidth}px` }}
			className={cx("grid", className)}
		>
			{data.map((item, index) => (
				<div
					key={item.key}
					ref={index === 0 ? firstItemRef : undefined}
					className={cx("item-container")}
				>
					<Item data={item} onClick={() => onClickItem?.(item)} />
				</div>
			))}
		</div>
	);
}
