export interface SeriesPoint { x: number; y: number }

export function buildLinePath(data: SeriesPoint[], width: number, height: number, pad=8){
  if(!data.length) return '';
  const xs = data.map(p=>p.x); const ys = data.map(p=>p.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const norm = (p: SeriesPoint) => ({
    x: ((p.x - minX) / (maxX - minX || 1)) * (width - pad*2) + pad,
    y: (1 - ((p.y - minY)/(maxY - minY || 1))) * (height - pad*2) + pad
  });
  return data.map((p,i)=>{ const {x,y} = norm(p); return `${i?'L':'M'}${x.toFixed(2)},${y.toFixed(2)}`; }).join(' ');
}

export function movingAverage(values: number[], window=3){
  if(window<=1) return values.slice();
  const out: number[] = [];
  for(let i=0;i<values.length;i++){
    const slice = values.slice(Math.max(0,i-window+1), i+1);
    out.push(slice.reduce((a,b)=>a+b,0)/slice.length);
  }
  return out;
}
