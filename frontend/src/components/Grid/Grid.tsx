import classNames from "classnames/bind";
import { useState } from "react";
import styles from "./Grid.module.css";

const cx = classNames.bind(styles);

type GridProps<T> = {
	data: Array<T & { key: string }>;
	Item: (props: T) => JSX.Element | null;
	onClickItem?: (item: T) => void;
	className?: string;
};

export function Grid<T>({ data, Item, className }: GridProps<T>) {
	const [itemWidth, setItemWidth] = useState<number>();
	const style = itemWidth
		? { ["--item-width" as string]: `${itemWidth}px` }
		: undefined;

	const itemRef = (item: HTMLDivElement | null) => {
		if (item && !itemWidth) {
			setItemWidth(item.offsetWidth);
		}
	};

	return (
		<div style={style} className={cx("grid", className)}>
			{data.map(({ key, ...item }, index) => (
				<div
					key={key}
					ref={index === 0 ? itemRef : undefined}
					className={cx("item-container")}
				>
					<Item {...(item as any)} />
				</div>
			))}
		</div>
	);
}
