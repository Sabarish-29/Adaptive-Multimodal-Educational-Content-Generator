import React from 'react';
interface SparkProps { values: number[]; width?: number; height?: number; stroke?: string }
export const Spark: React.FC<SparkProps> = ({ values, width=100, height=28, stroke='#10B981' }) => {
  if(!values.length) return <span style={{fontSize:10, opacity:.6}}>No data</span>;
  const min = Math.min(...values); const max = Math.max(...values);
  const pts = values.map((v,i)=>{
    const x = (i/(values.length-1||1)) * (width-4) + 2;
    const y = (1 - (v - min)/(max-min || 1)) * (height-4) + 2;
    return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`;
  }).join(' ');
  return <svg width={width} height={height} role="img" aria-label="spark line" style={{ display:'block' }}><path d={pts} fill="none" stroke={stroke} strokeWidth={2} /></svg>;
};
