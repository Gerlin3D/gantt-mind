import type { TimelineDay } from '../utils/dateUtils';

type TimelineHeaderProps = {
  days: TimelineDay[];
};

export function TimelineHeader({ days }: TimelineHeaderProps) {
  return (
    <div className="timeline-header" role="row" aria-label="Timeline days">
      {days.map((day) => (
        <div
          className={[
            'timeline-day-header',
            day.isWeekend ? 'is-weekend' : '',
            day.isToday ? 'is-today' : '',
            day.isMonthStart ? 'is-month-start' : '',
          ]
            .filter(Boolean)
            .join(' ')}
          key={day.isoDate}
          role="columnheader"
        >
          {day.isMonthStart ? <span className="month-label">{day.monthLabel}</span> : null}
          <span>{day.weekdayShort}</span>
          <strong>{day.day}</strong>
        </div>
      ))}
    </div>
  );
}
