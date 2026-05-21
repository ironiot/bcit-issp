import classNames from "classnames/bind";
import styles from "./Button.module.css";

const cx = classNames.bind(styles);

type Props = {
	text: string;
	onClick?: () => void;
	disabled?: boolean;
};

export function Button({ text, onClick, disabled }: Props) {
	return (
		<button
			type="button"
			className={cx("button")}
			onClick={onClick}
			disabled={disabled}
		>
			{text}
		</button>
	);
}
