import type { ReactNode, SVGProps } from "react";

type IconName = "arrow" | "check" | "copy" | "download" | "link" | "moon" | "music" | "sun" | "wave";

interface IconProps extends SVGProps<SVGSVGElement> {
  name: IconName;
}

export function Icon({ name, ...props }: IconProps) {
  const commonProps = {
    fill: "none",
    stroke: "currentColor",
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    strokeWidth: 1.8,
    viewBox: "0 0 24 24",
    "aria-hidden": true,
    ...props,
  };

  const paths: Record<IconName, ReactNode> = {
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    check: <path d="m5 12 4.2 4.2L19.5 6" />,
    copy: <><rect x="8" y="8" width="11" height="11" rx="2" /><path d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h2" /></>,
    download: <><path d="M12 3v11m0 0 4-4m-4 4-4-4" /><path d="M5 19h14" /></>,
    link: <><path d="M10.6 13.4a4 4 0 0 0 5.66 0l2.12-2.12a4 4 0 0 0-5.66-5.66l-1.21 1.2" /><path d="M13.4 10.6a4 4 0 0 0-5.66 0l-2.12 2.12a4 4 0 0 0 5.66 5.66l1.2-1.2" /></>,
    moon: <path d="M20.8 14.5A8.6 8.6 0 0 1 9.5 3.2 8.6 8.6 0 1 0 20.8 14.5Z" />,
    music: <><path d="M9 18V5l10-2v13" /><circle cx="6" cy="18" r="3" /><circle cx="16" cy="16" r="3" /></>,
    sun: <><circle cx="12" cy="12" r="3.5" /><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" /></>,
    wave: <path d="M3 12c2.25 0 2.75-5 5-5s2.75 10 5 10 2.75-5 5-5h3" />,
  };

  return <svg {...commonProps}>{paths[name]}</svg>;
}
