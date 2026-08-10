import './ProgressBar.css';

interface ProgressBarProps {
  value: number; // 0..100
  label?: string;
}

/** An accessible progress bar with a numeric label. */
export function ProgressBar({ value, label }: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="progress">
      <div className="progress__head">
        <span>{label ?? 'Progress'}</span>
        <span className="progress__pct">{clamped}%</span>
      </div>
      <div
        className="progress__track"
        role="progressbar"
        aria-valuenow={clamped}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Progress'}
      >
        <div className="progress__fill" style={{ width: `${clamped}%` }} />
      </div>
    </div>
  );
}
