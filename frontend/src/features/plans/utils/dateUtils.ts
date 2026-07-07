import type { PlanDto, TaskDto } from '../model/types';

const dayMs = 24 * 60 * 60 * 1000;

export type DateOnly = {
  year: number;
  month: number;
  day: number;
};

export type TimelineDay = DateOnly & {
  isoDate: string;
  weekdayShort: string;
  monthLabel: string;
  isWeekend: boolean;
  isToday: boolean;
  isMonthStart: boolean;
};

export type PlanDateRange = {
  start: string;
  end: string;
};

export function parseDateOnly(isoDate: string): DateOnly {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(isoDate);

  if (!match) {
    throw new Error(`Invalid date-only value: ${isoDate}`);
  }

  return {
    year: Number(match[1]),
    month: Number(match[2]),
    day: Number(match[3]),
  };
}

function toUtcMs(date: DateOnly) {
  return Date.UTC(date.year, date.month - 1, date.day);
}

function fromUtcMs(value: number): DateOnly {
  const date = new Date(value);

  return {
    year: date.getUTCFullYear(),
    month: date.getUTCMonth() + 1,
    day: date.getUTCDate(),
  };
}

export function toIsoDate(date: DateOnly) {
  return `${date.year.toString().padStart(4, '0')}-${date.month
    .toString()
    .padStart(2, '0')}-${date.day.toString().padStart(2, '0')}`;
}

export function addCalendarDays(isoDate: string, days: number) {
  const date = parseDateOnly(isoDate);

  return toIsoDate(fromUtcMs(toUtcMs(date) + days * dayMs));
}

export function differenceInCalendarDays(fromIsoDate: string, toIsoDateValue: string) {
  const from = parseDateOnly(fromIsoDate);
  const to = parseDateOnly(toIsoDateValue);

  return Math.round((toUtcMs(to) - toUtcMs(from)) / dayMs);
}

export function formatDate(isoDate: string) {
  const date = parseDateOnly(isoDate);

  return `${date.day.toString().padStart(2, '0')}.${date.month
    .toString()
    .padStart(2, '0')}.${date.year}`;
}

export function findPlanDateRange(plan: PlanDto): PlanDateRange | null {
  if (plan.tasks.length === 0) {
    return null;
  }

  const starts = plan.tasks.map((task) => task.start_date);
  const ends = plan.tasks.map((task) => task.end_date);

  return {
    start: starts.reduce((earliest, value) =>
      differenceInCalendarDays(value, earliest) > 0 ? value : earliest,
    ),
    end: ends.reduce((latest, value) =>
      differenceInCalendarDays(latest, value) > 0 ? value : latest,
    ),
  };
}

export function generateTimelineDays(startIsoDate: string, endIsoDate: string) {
  const totalDays = differenceInCalendarDays(startIsoDate, endIsoDate);
  const todayIsoDate = toIsoDate(fromUtcMs(Date.now()));

  return Array.from({ length: totalDays + 1 }, (_, index): TimelineDay => {
    const isoDate = addCalendarDays(startIsoDate, index);
    const date = parseDateOnly(isoDate);
    const utcDate = new Date(toUtcMs(date));
    const weekday = utcDate.getUTCDay();

    return {
      ...date,
      isoDate,
      weekdayShort: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][weekday],
      monthLabel: utcDate.toLocaleString('en-US', {
        month: 'short',
        year: 'numeric',
        timeZone: 'UTC',
      }),
      isWeekend: weekday === 0 || weekday === 6,
      isToday: isoDate === todayIsoDate,
      isMonthStart: date.day === 1 || index === 0,
    };
  });
}

export function calculateTaskOffset(timelineStart: string, task: TaskDto) {
  return differenceInCalendarDays(timelineStart, task.start_date);
}

export function calculateTaskWidth(task: TaskDto) {
  return task.duration_days;
}

export function buildTimelineRange(plan: PlanDto, paddingDays = 2): PlanDateRange | null {
  const range = findPlanDateRange(plan);

  if (!range) {
    return null;
  }

  return {
    start: addCalendarDays(range.start, -paddingDays),
    end: addCalendarDays(range.end, paddingDays),
  };
}

export function sortTasksByPosition(tasks: TaskDto[]) {
  return [...tasks].sort((left, right) => left.position - right.position || left.id.localeCompare(right.id));
}
