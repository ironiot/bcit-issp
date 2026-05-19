import { Backdrop, Modal as MUIModal } from "@mui/material";
import type { ReactNode } from "react";

type ModalProps = {
	open: boolean;
	onClose: () => void;
	children: ReactNode;
};

export function Modal({ open, onClose, children }: ModalProps) {
	return (
		<MUIModal
			open={open}
			onClose={onClose}
			slots={{ backdrop: Backdrop }}
			slotProps={{
				backdrop: { sx: { backgroundColor: "rgba(0, 0, 0, 0.65)" } },
			}}
		>
			<div
				style={{
					position: "absolute",
					top: "50%",
					left: "50%",
					transform: "translate(-50%, -50%)",
					width: "80vw",
					maxHeight: "80vh",
					overflow: "auto",
				}}
			>
				{children}
			</div>
		</MUIModal>
	);
}
