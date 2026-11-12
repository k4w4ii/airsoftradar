// Egyszerű vonalas ikonok a kalkulátorokhoz (currentColor, külső fájl nélkül).
const PATHS = {
  bolt: <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z" />,
  spring: <path d="M6 3h12M6 21h12M7 6c5 0 5 2.5 10 2.5M7 10.5c5 0 5 2.5 10 2.5M7 15c5 0 5 2.5 10 2.5" />,
  cylinder: <><ellipse cx="12" cy="5" rx="6" ry="2.5" /><path d="M6 5v14c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5V5M6 12c0 1.4 2.7 2.5 6 2.5s6-1.1 6-2.5" /></>,
  battery: <><rect x="3" y="7" width="16" height="10" rx="2" /><path d="M21 10v4M8 10l-2 2.5h4L8 15" /></>,
  calc: <><rect x="5" y="2.5" width="14" height="19" rx="2" /><path d="M8 6h8v3H8zM8.5 13h.01M12 13h.01M15.5 13h.01M8.5 17h.01M12 17h.01M15.5 17h.01" /></>,
};

export default function ToolIcon({ name, size = 22 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8"
         strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PATHS[name] || PATHS.calc}
    </svg>
  );
}
