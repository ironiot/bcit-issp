import classNames from "classnames/bind";
import { useEffect, useRef } from "react";
import styles from "./Grid.module.css";

const cx = classNames.bind(styles);

type GridProps<T> = {
	data: Array<T & { key: string }>;
	Item: (props: T) => JSX.Element | null;
	className?: string;
};

export function Grid<T>({ data, Item, className }: GridProps<T>) {
	const containerRef = useRef<HTMLDivElement>(null);
	const firstItemRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		const container = containerRef.current;
		if (!container || !firstItemRef.current) return;

		const updateItemWidth = () => {
			const itemWidth = firstItemRef.current?.offsetWidth;
			if (itemWidth && itemWidth > 0) {
				container.style.setProperty("--item-width", `${itemWidth}px`);
			}
		};

		// Initial measurement
		updateItemWidth();

		// Set up ResizeObserver to remeasure on container resize
		const resizeObserver = new ResizeObserver(() => {
			updateItemWidth();
		});

		resizeObserver.observe(container);

		return () => {
			resizeObserver.disconnect();
		};
	}, []);

	return (
		<div
			ref={containerRef}
			style={{
				["--gap" as string]: "32px",
			}}
			className={cx("grid", className)}
		>
			{data.map((item, index) => (
				<div
					key={item.key}
					ref={index === 0 ? firstItemRef : undefined}
					className={cx("item-container")}
				>
					<Item {...item} />
				</div>
			))}
		</div>
	);
}
