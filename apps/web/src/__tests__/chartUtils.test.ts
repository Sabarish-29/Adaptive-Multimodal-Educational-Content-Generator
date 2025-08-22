import { buildLinePath, movingAverage } from '../components/charts/utils';

describe('chart utils', () => {
  test('buildLinePath creates path for simple series', () => {
    const path = buildLinePath([{x:0,y:0},{x:1,y:1}], 100, 40);
    expect(path.startsWith('M')).toBe(true);
    expect(path.includes('L')).toBe(true);
  });
  test('buildLinePath empty returns empty string', () => {
    expect(buildLinePath([], 100, 40)).toBe('');
  });
  test('movingAverage computes rolling mean', () => {
    const avg = movingAverage([2,4,6,8], 2); // window 2
    expect(avg).toEqual([2, (2+4)/2, (4+6)/2, (6+8)/2]);
  });
  test('movingAverage window 1 returns same array', () => {
    const vals = [1,2,3];
    expect(movingAverage(vals,1)).toEqual(vals);
  });
});
