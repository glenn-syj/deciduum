import { useMemo, useState } from 'react';

export type TimelineItemType = 'origin' | 'review' | 'log' | 'task' | 'memo';

export interface TimelineItem {
  id: string;
  type: TimelineItemType;
  date: string;
  title: string;
  content?: string;
  status?: string;
  logType?: string;
}

interface TimelineProps {
  items: TimelineItem[];
  currentStatus?: string;
}

// Text labels for each item type
const TYPE_LABELS: Record<string, string> = {
  origin: 'Started',
  review: 'Review',
  note: 'Note',
  reflection: 'Reflection',
  task: 'Task',
  memo: 'Memo',
  state_change: 'Status changed',
  current: 'Now',
};

// Colors for each type (text and accent)
interface TypeColors {
  labelColor: string;
  accentColor: string;
}

const TYPE_COLORS: Record<string, TypeColors> = {
  origin: { labelColor: '#6b7280', accentColor: '#9ca3af' },
  review: { labelColor: '#8b5cf6', accentColor: '#8b5cf6' },
  note: { labelColor: '#3b82f6', accentColor: '#3b82f6' },
  reflection: { labelColor: '#ec4899', accentColor: '#ec4899' },
  task: { labelColor: '#f59e0b', accentColor: '#f59e0b' },
  memo: { labelColor: '#0891b2', accentColor: '#0891b2' },
  state_change: { labelColor: '#6b7280', accentColor: '#6b7280' },
  current: { labelColor: '#6b7280', accentColor: '#6b7280' },
};

const getTypeLabel = (item: TimelineItem): string => {
  if (item.type === 'origin') return TYPE_LABELS.origin;
  if (item.type === 'review') return TYPE_LABELS.review;
  if (item.type === 'memo') return TYPE_LABELS.memo;
  if (item.type === 'task') return TYPE_LABELS.task;
  if (item.type === 'log') {
    if (item.logType === 'reflection') return TYPE_LABELS.reflection;
    if (item.logType === 'state_change') return TYPE_LABELS.state_change;
  }
  return TYPE_LABELS.note;
};

const getTypeColors = (item: TimelineItem): TypeColors => {
  if (item.type === 'origin') return TYPE_COLORS.origin;
  if (item.type === 'review') return TYPE_COLORS.review;
  if (item.type === 'memo') return TYPE_COLORS.memo;
  if (item.type === 'task') return TYPE_COLORS.task;
  if (item.type === 'log') {
    if (item.logType === 'reflection') return TYPE_COLORS.reflection;
    if (item.logType === 'state_change') return TYPE_COLORS.state_change;
  }
  return TYPE_COLORS.note;
};

// Status colors for the "Now" indicator
const STATUS_COLORS: Record<string, string> = {
  ongoing: '#3b82f6',
  completed: '#10b981',
  archived: '#6b7280',
};

const formatShortDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', { month: 'short', day: '2-digit' });
};

export default function Timeline({ items, currentStatus = 'ongoing' }: TimelineProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const sortedItems = useMemo(() => {
    return [...items].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [items]);

  const handleItemClick = (item: TimelineItem) => {
    if (item.content || item.type === 'origin' || item.type === 'review') {
      setExpandedId(expandedId === item.id ? null : item.id);
    }
  };

  return (
    <div className="timeline-vertical">
      {sortedItems.map((item, index) => {
        const typeColors = getTypeColors(item);
        
        return (
          <div key={item.id} className="timeline-vertical-item">
            {/* Connector line */}
            {index > 0 && <div className="timeline-vertical-connector" />}

            {/* Item card */}
            <div
              className={`timeline-vertical-card ${expandedId === item.id ? 'expanded' : ''}`}
              onClick={() => handleItemClick(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleItemClick(item)}
            >
              {/* Date and type label row */}
              <div className="timeline-vertical-header">
                <span 
                  className="timeline-vertical-date"
                  style={{ color: typeColors.accentColor }}
                >
                  {formatShortDate(item.date)}
                </span>
                <span 
                  className="timeline-vertical-type"
                  style={{ color: typeColors.labelColor }}
                >
                  {getTypeLabel(item)}
                </span>
              </div>

              {/* Title */}
              <div className="timeline-vertical-title">{item.title}</div>

              {/* Content (expandable) */}
              {item.content && (
                <div className={`timeline-vertical-content ${expandedId === item.id ? 'expanded' : ''}`}>
                  {item.content}
                </div>
              )}

              {/* Click hint if content is long */}
              {item.content && item.content.length > 100 && (
                <div className="timeline-vertical-hint">
                  {expandedId === item.id ? 'Show less' : 'Show more'}
                </div>
              )}
            </div>
          </div>
        );
      })}

      {/* Current status indicator */}
      <div className="timeline-vertical-item">
        <div className="timeline-vertical-connector" />
        
        <div className={`timeline-vertical-card current status-${currentStatus}`}>
          <div className="timeline-vertical-header">
            <span 
              className="timeline-vertical-date"
              style={{ color: STATUS_COLORS[currentStatus as keyof typeof STATUS_COLORS] || STATUS_COLORS.ongoing }}
            >
              Now
            </span>
            <span 
              className="timeline-vertical-type"
              style={{ color: STATUS_COLORS[currentStatus as keyof typeof STATUS_COLORS] || STATUS_COLORS.ongoing }}
            >
              {currentStatus}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
