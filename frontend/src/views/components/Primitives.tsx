import { useEffect, useId, useRef, type ReactNode } from "react";
import { AlertCircle, Info, LoaderCircle, X } from "lucide-react";

export function ErrorNotice({
  children,
  action,
}: {
  children?: ReactNode;
  action?: ReactNode;
}) {
  if (!children) return null;
  return (
    <div className="notice notice-error" role="alert">
      <AlertCircle size={17} />
      <div>{children}</div>
      {action}
    </div>
  );
}
export function InfoNotice({
  children,
  onClose,
}: {
  children?: ReactNode;
  onClose?: () => void;
}) {
  if (!children) return null;
  return (
    <div className="notice notice-info" role="status">
      <Info size={17} />
      <div>{children}</div>
      {onClose && (
        <button
          className="icon-button"
          aria-label="안내 닫기"
          onClick={onClose}
        >
          <X size={15} />
        </button>
      )}
    </div>
  );
}
export function Loading({ label = "불러오는 중" }: { label?: string }) {
  return (
    <div className="loading" role="status">
      <LoaderCircle className="spinner" size={19} />
      <span>{label}</span>
    </div>
  );
}
export function EmptyState({
  icon,
  title,
  children,
}: {
  icon?: ReactNode;
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty-state">
      {icon && <div className="empty-icon">{icon}</div>}
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function Modal({
  title,
  eyebrow,
  children,
  onClose,
  className = "",
}: {
  title: string;
  eyebrow?: string;
  children: ReactNode;
  onClose: () => void;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={`modal ${className}`}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
    >
      <header className="modal-header">
        <div>
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h2 id={titleId}>{title}</h2>
        </div>
        <button className="icon-button" onClick={onClose} aria-label="닫기">
          <X size={20} />
        </button>
      </header>
      {children}
    </dialog>
  );
}
export function Toggle({
  checked,
  onChange,
  label,
  disabled,
  description,
}: {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  disabled?: boolean;
  description?: string;
}) {
  const id = useId();
  return (
    <div className="toggle-row">
      <label htmlFor={id}>
        <strong>{label}</strong>
        {description && <span>{description}</span>}
      </label>
      <button
        id={id}
        type="button"
        className={`switch ${checked ? "is-on" : ""}`}
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
      >
        <span />
      </button>
    </div>
  );
}
export function Badge({
  children,
  tone = "",
}: {
  children: ReactNode;
  tone?: "blue" | "green" | "amber" | "red" | "";
}) {
  return (
    <span className={`badge ${tone ? `badge-${tone}` : ""}`}>{children}</span>
  );
}
