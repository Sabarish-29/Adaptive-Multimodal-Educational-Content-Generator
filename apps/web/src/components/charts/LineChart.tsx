import React from 'react';
import { buildLinePath, SeriesPoint } from './utils';

interface LineChartProps { data: SeriesPoint[]; width?: number; height?: number; stroke?: string; }

export const LineChart: React.FC<LineChartProps> = ({ data, width=260, height=120, stroke='#6366F1' }) => {
  if(!data.length) return <div style={{fontSize:12, opacity:.6}}>No data</div>;
  const path = buildLinePath(data, width, height);
  return <svg width={width} height={height} role="img" aria-label="line chart" style={{ display:'block', maxWidth:'100%' }}><path d={path} fill="none" stroke={stroke} strokeWidth={2} /></svg>;
};
