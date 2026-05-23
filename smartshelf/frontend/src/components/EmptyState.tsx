import type { KeyboardEvent, ReactNode } from "react";

type EmptyStateAction = {
  label: string;
  onClick: () => void;
};

type EmptyStateProps = {
  title: string;
  subtitle: string;
  action: EmptyStateAction;
  meta?: { label: string; value: string }[];
  guidance?: string[];
  children?: ReactNode;
};

export default function EmptyState({
  title,
  subtitle,
  action,
  meta = [],
  guidance = [],
  children,
}: EmptyStateProps) {
  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      action.onClick();
    }
  };

  return (
    <section className="onboarding-empty-wrap" aria-label={title}>
      <article
        className="onboarding-empty-card"
        role="button"
        tabIndex={0}
        onClick={action.onClick}
        onKeyDown={handleKeyDown}
      >
        <div className="onboarding-empty-copy">
          <span className="onboarding-eyebrow">Get started</span>
          <h2>{title}</h2>
          <p>{subtitle}</p>
        </div>

        {meta.length > 0 && (
          <div className="onboarding-meta-grid" aria-label="Platform highlights">
            {meta.map((item) => (
              <div className="onboarding-meta-card" key={item.label}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        )}

        {guidance.length > 0 && (
          <div className="onboarding-steps" aria-label="How it works">
            {guidance.map((item, index) => (
              <div className="onboarding-step" key={item}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{item}</strong>
              </div>
            ))}
          </div>
        )}

        <button
          type="button"
          className="onboarding-primary-btn"
          onClick={(event) => {
            event.stopPropagation();
            action.onClick();
          }}
        >
          {action.label}
        </button>
      </article>

      {children}
    </section>
  );
}
