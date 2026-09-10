type Status = "online" | "offline" | "warning" | "unknown";

const labels: Record<Status, string> = {
  online: "En ligne",
  offline: "Hors ligne",
  warning: "Alerte",
  unknown: "Inconnu",
};

const colors: Record<Status, string> = {
  online: "bg-status-online",
  offline: "bg-status-offline",
  warning: "bg-status-warning",
  unknown: "bg-status-unknown",
};

export function StatusDot({ status }: { status: Status }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm text-muted">
      <span className={`w-1.5 h-1.5 rounded-full ${colors[status]}`} />
      {labels[status]}
    </span>
  );
}