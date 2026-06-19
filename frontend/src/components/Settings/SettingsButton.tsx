interface SettingsButtonProps {
  onClick: () => void;
  activeCount: number;
  totalCount: number;
}

export function SettingsButton({ onClick, activeCount, totalCount }: SettingsButtonProps) {
  return (
    <button className="settings-button" onClick={onClick} aria-label="Configure real-data sources">
      <span className="gear" aria-hidden>
        ⚙
      </span>
      <span className="settings-button-text">
        Data Sources
        <em>
          {activeCount}/{totalCount} active
        </em>
      </span>
    </button>
  );
}
