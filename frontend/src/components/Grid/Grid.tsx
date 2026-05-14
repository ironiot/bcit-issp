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

	return (
		<div style={style} className={cx("grid", className)}>
			{data.map((item, index) => (
				<div
					key={item.key}
					ref={
						index === 0
							? (item) => item && setItemWidth(item.offsetWidth)
							: undefined
					}
					className={cx("item-container")}
				>
					<Item {...item} />
				</div>
			))}
		</div>
	);
}
