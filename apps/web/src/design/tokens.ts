// Design tokens (initial scaffold) – extend as needed.
export const colors = {
  bg: '#0F1115',
  bgAlt: '#161A21',
  bgElevated: '#1F252E',
  border: '#2A303B',
  focus: '#3B82F6',
  text: '#F5F7FA',
  textDim: '#B4BCC8',
  accent: '#6366F1',
  accentHover: '#818CF8',
  danger: '#EF4444',
  warn: '#F59E0B',
  success: '#10B981',
};

export const radii = {
  sm: '4px',
  md: '8px',
  lg: '14px',
  pill: '999px'
};

export const space = {
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '20px',
  xl: '32px'
};

export const font = {
  stack: `Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif`,
  mono: `ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', monospace`,
  size: {
    xs: '12px',
    sm: '14px',
    md: '16px',
    lg: '20px',
    xl: '28px',
    xxl: '36px'
  },
  line: {
    tight: 1.1,
    normal: 1.4,
    relaxed: 1.6
  },
  weight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700
  }
};

export const shadows = {
  sm: '0 1px 2px rgba(0,0,0,0.2)',
  md: '0 4px 12px -2px rgba(0,0,0,0.35)',
  ring: '0 0 0 1px rgba(255,255,255,0.08)',
};

export const transitions = {
  fast: '120ms cubic-bezier(.4,0,.2,1)',
  normal: '200ms cubic-bezier(.4,0,.2,1)'
};

export const z = {
  base: 0,
  dropdown: 10,
  toast: 100,
  modal: 1000
};

export const layout = {
  contentMaxWidth: '1180px'
};

export const darkThemeVars = { colors, radii, space, font, shadows, transitions, z, layout };
