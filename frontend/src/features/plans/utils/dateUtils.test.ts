import { describe, expect, it } from 'vitest';
import { demoPlanFixture } from '../../../test/planFixtures';
import {
  buildTimelineRange,
  calculateTaskOffset,
  calculateTaskWidth,
  differenceInCalendarDays,
  findPlanDateRange,
  formatDate,
  generateTimelineDays,
} from './dateUtils';

describe('dateUtils', () => {
  it('finds a plan date range from task dates', () => {
    expect(findPlanDateRange(demoPlanFixture)).toEqual({
      start: '2026-01-05',
      end: '2026-01-10',
    });
  });

  it('calculates one-day task width from duration days', () => {
    expect(calculateTaskWidth(demoPlanFixture.tasks[2])).toBe(1);
  });

  it('calculates task offset from the padded timeline start', () => {
    expect(calculateTaskOffset('2026-01-03', demoPlanFixture.tasks[0])).toBe(2);
  });

  it('generates days across month boundaries without local timezone shift', () => {
    const days = generateTimelineDays('2026-01-30', '2026-02-02');

    expect(days.map((day) => day.isoDate)).toEqual([
      '2026-01-30',
      '2026-01-31',
      '2026-02-01',
      '2026-02-02',
    ]);
    expect(formatDate('2026-02-01')).toBe('01.02.2026');
  });

  it('calculates calendar day differences from date-only values', () => {
    expect(differenceInCalendarDays('2026-01-31', '2026-02-02')).toBe(2);
  });

  it('adds visual padding to the timeline range', () => {
    expect(buildTimelineRange(demoPlanFixture)).toEqual({
      start: '2026-01-03',
      end: '2026-01-12',
    });
  });
});
