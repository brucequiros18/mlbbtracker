import type { SVGProps } from 'react'

/** Inline icons - no icon font, no extra request. */

type IconProps = SVGProps<SVGSVGElement> & { size?: number }

function Icon({ size = 20, children, ...props }: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      {children}
    </svg>
  )
}

export const HomeIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M3 10.5 12 3l9 7.5" />
    <path d="M5 9.8V20h14V9.8" />
    <path d="M9.5 20v-5.5h5V20" />
  </Icon>
)

export const PlayersIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="9" cy="8" r="3.2" />
    <path d="M3 20c0-3.2 2.7-5.2 6-5.2s6 2 6 5.2" />
    <path d="M16.5 11.2a3 3 0 1 0-1.2-5.7" />
    <path d="M17.5 14.4c2.1.5 3.5 2.1 3.5 4.4" />
  </Icon>
)

export const HeroesIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M12 3 20 6v5.5c0 4.6-3.2 8.3-8 9.5-4.8-1.2-8-4.9-8-9.5V6l8-3Z" />
    <path d="m9 12 2.2 2.2L15.5 10" />
  </Icon>
)

export const RanksIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M4 20V10" />
    <path d="M10 20V4" />
    <path d="M16 20v-7" />
    <path d="M22 20H2" />
  </Icon>
)

export const SavedIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M6.5 4h11a1.5 1.5 0 0 1 1.5 1.5V21l-7-4-7 4V5.5A1.5 1.5 0 0 1 6.5 4Z" />
  </Icon>
)

export const TrophyIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M8 4h8v4.5a4 4 0 0 1-8 0V4Z" />
    <path d="M8 6H5.5A1.5 1.5 0 0 0 4 7.5C4 9.4 5.6 11 7.5 11" />
    <path d="M16 6h2.5A1.5 1.5 0 0 1 20 7.5C20 9.4 18.4 11 16.5 11" />
    <path d="M12 12.5V16" />
    <path d="M8.5 20h7" />
    <path d="M10 16h4v4h-4z" />
  </Icon>
)

export const SearchIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="11" cy="11" r="6.5" />
    <path d="m16 16 4.5 4.5" />
  </Icon>
)

export const RefreshIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M20 11a8 8 0 1 0-.7 4.5" />
    <path d="M20 4v7h-7" />
  </Icon>
)

export const ChevronRightIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m9 5 7 7-7 7" />
  </Icon>
)

export const ChevronLeftIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m15 5-7 7 7 7" />
  </Icon>
)

export const CloseIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m6 6 12 12M18 6 6 18" />
  </Icon>
)

export const SunIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="4" />
    <path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4" />
  </Icon>
)

export const MoonIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5Z" />
  </Icon>
)

export const DownloadIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M12 3v10" />
    <path d="m8 9 4 4 4-4" />
    <path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
  </Icon>
)

export const LogoutIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3" />
    <path d="M10 16l-4-4 4-4" />
    <path d="M6 12h9" />
  </Icon>
)

export const UserIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="12" cy="8" r="3.6" />
    <path d="M4.5 20c0-3.8 3.3-6.2 7.5-6.2s7.5 2.4 7.5 6.2" />
  </Icon>
)

export const WifiOffIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m3 3 18 18" />
    <path d="M8.5 14.5a5 5 0 0 1 6 0" />
    <path d="M5 11a9.5 9.5 0 0 1 3.2-1.9" />
    <path d="M15.6 9.3A9.5 9.5 0 0 1 19 11" />
    <path d="M2 7.5A14 14 0 0 1 6.5 5" />
    <path d="M17.5 5A14 14 0 0 1 22 7.5" />
    <path d="M12 19h.01" />
  </Icon>
)

export const InfoIcon = (props: IconProps) => (
  <Icon {...props}>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5" />
    <path d="M12 8h.01" />
  </Icon>
)

export const TrendUpIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m3 16 5.5-5.5 3.5 3.5L21 5" />
    <path d="M15 5h6v6" />
  </Icon>
)

export const TrendDownIcon = (props: IconProps) => (
  <Icon {...props}>
    <path d="m3 8 5.5 5.5L12 10l9 9" />
    <path d="M15 19h6v-6" />
  </Icon>
)
