type PlayerControlsProps = {
  title: string;
  isPlaying: boolean;
  currentTimeMs: number;
  durationMs: number;
  rate: number;
  onPlay: () => void;
  onPause: () => void;
  onSeek: (nextMs: number) => void;
  onRateChange: (nextRate: number) => void;
};

function formatClock(ms: number) {
  const totalSeconds = Math.max(Math.floor(ms / 1000), 0);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

export function PlayerControls({
  title,
  isPlaying,
  currentTimeMs,
  durationMs,
  rate,
  onPlay,
  onPause,
  onSeek,
  onRateChange,
}: PlayerControlsProps) {
  const safeDurationMs = Math.max(durationMs, 1);

  return (
    <section className="control-panel">
      <div className="control-card">
        <div className="control-copy">
          <p className="eyebrow">Now Playing</p>
          <h2 className="control-title">{title}</h2>
          <p className="control-subtitle">
            Mock front-end flow wired to a local mp3 fixture.
          </p>
        </div>

        <div className="control-row">
          <button className="primary-button" type="button" onClick={onPlay}>
            {isPlaying ? "Resume" : "Play"}
          </button>
          <button className="secondary-button" type="button" onClick={onPause}>
            Pause
          </button>
        </div>

        <div className="time-row">
          <span>{formatClock(currentTimeMs)}</span>
          <span>{formatClock(durationMs)}</span>
        </div>

        <div className="progress-block">
          <label className="progress-label" htmlFor="progress">
            Progress
          </label>
          <input
            id="progress"
            type="range"
            min="0"
            max={safeDurationMs}
            value={Math.min(currentTimeMs, safeDurationMs)}
            onChange={(event) => onSeek(Number(event.target.value))}
          />
        </div>

        <div className="progress-block">
          <div className="progress-header">
            <label className="progress-label" htmlFor="rate">
              Speed
            </label>
            <span className="progress-value">{rate.toFixed(2)}x</span>
          </div>
          <input
            id="rate"
            type="range"
            min="0.8"
            max="1.4"
            step="0.05"
            value={rate}
            onChange={(event) => onRateChange(Number(event.target.value))}
          />
        </div>
      </div>
    </section>
  );
}
