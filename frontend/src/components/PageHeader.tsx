export function PageHeader({
  path,
  title,
  subtitle,
}: {
  path: string;
  title: string;
  subtitle?: string;
}) {
  return (
    <div className="mb-8">
      <p className="text-xs font-mono text-muted mb-2">{path}</p>
      <h1 className="text-xl font-medium text-ink">{title}</h1>
      {subtitle && <p className="text-sm text-muted mt-1">{subtitle}</p>}
    </div>
  );
}