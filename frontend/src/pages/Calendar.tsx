import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { decisionsApi, memosApi, tasksApi, Decision, Memo, Task } from '../utils/api';

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end?: string;
  backgroundColor: string;
  borderColor: string;
  extendedProps: {
    type: 'decision' | 'memo' | 'task';
    data: Decision | Memo | Task;
  };
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength - 3) + '...';
}

export default function Calendar() {

  // Fetch all data sources
  const { data: decisionsData, isLoading: decisionsLoading, error: decisionsError } = useQuery({
    queryKey: ['decisions'],
    queryFn: async () => {
      const response = await decisionsApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  const { data: memosData, isLoading: memosLoading, error: memosError } = useQuery({
    queryKey: ['memos'],
    queryFn: async () => {
      const response = await memosApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  const { data: tasksData, isLoading: tasksLoading, error: tasksError } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await tasksApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
  });

  const isLoading = decisionsLoading || memosLoading || tasksLoading;
  const error = decisionsError || memosError || tasksError;

  // Transform data into calendar events
  const events = useMemo<CalendarEvent[]>(() => {
    const calendarEvents: CalendarEvent[] = [];

    // Add decisions
    decisionsData?.forEach((decision: Decision) => {
      if (decision.date) {
        calendarEvents.push({
          id: `decision-${decision.id}`,
          title: truncateText(decision.title, 50),
          start: decision.date,
          backgroundColor: '#3b82f6',
          borderColor: '#2563eb',
          extendedProps: {
            type: 'decision',
            data: decision,
          },
        });
      }
    });

    // Add memos
    memosData?.forEach((memo: Memo) => {
      if (memo.date) {
        calendarEvents.push({
          id: `memo-${memo.id}`,
          title: truncateText(memo.content, 50),
          start: memo.date,
          backgroundColor: '#22c55e',
          borderColor: '#16a34a',
          extendedProps: {
            type: 'memo',
            data: memo,
          },
        });
      }
    });

    // Add tasks
    tasksData?.forEach((task: Task) => {
      if (task.due_date) {
        calendarEvents.push({
          id: `task-${task.id}`,
          title: truncateText(task.title, 50),
          start: task.due_date,
          backgroundColor: '#f97316',
          borderColor: '#ea580c',
          extendedProps: {
            type: 'task',
            data: task,
          },
        });
      }
    });

    return calendarEvents;
  }, [decisionsData, memosData, tasksData]);

  const handleEventClick = (info: any) => {
    const event = info.event;
    const { type, data } = event.extendedProps;
    
    let message = '';
    switch (type) {
      case 'decision':
        const decision = data as Decision;
        message = `Decision: ${decision.title}\nStatus: ${decision.status}\nDate: ${decision.date}`;
        break;
      case 'memo':
        const memo = data as Memo;
        message = `Memo: ${memo.content}\nDate: ${memo.date}`;
        break;
      case 'task':
        const task = data as Task;
        message = `Task: ${task.title}\nStatus: ${task.status}\nDue: ${task.due_date}`;
        break;
    }
    
    alert(message);
  };

  const getErrorMessage = (err: unknown): string => {
    if (!err) return 'Unknown error';
    if (err instanceof Error) return err.message;
    if (typeof err === 'object' && err !== null && 'message' in err) return String((err as { message: unknown }).message);
    return String(err);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Calendar</h1>
      </div>
      
      {isLoading && (
        <div className="loading">Loading calendar events...</div>
      )}

      {error && (
        <div className="error-message" style={{ padding: '1rem', backgroundColor: '#fee2e2', border: '1px solid #ef4444', borderRadius: '4px', marginBottom: '1rem' }}>
          <p style={{ color: '#dc2626', fontWeight: 'bold' }}>Failed to load calendar events</p>
          <p style={{ color: '#991b1b', fontSize: '0.875rem' }}>Error: {getErrorMessage(error)}</p>
          {decisionsError && <p style={{ color: '#991b1b', fontSize: '0.75rem' }}>Decisions API: {getErrorMessage(decisionsError)}</p>}
          {memosError && <p style={{ color: '#991b1b', fontSize: '0.75rem' }}>Memos API: {getErrorMessage(memosError)}</p>}
          {tasksError && <p style={{ color: '#991b1b', fontSize: '0.75rem' }}>Tasks API: {getErrorMessage(tasksError)}</p>}
        </div>
      )}
      
      <div className="calendar-container">
        <FullCalendar
          plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
          initialView="dayGridMonth"
          headerToolbar={{
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
          }}
          events={events}
          eventClick={handleEventClick}
          height="auto"
          aspectRatio={1.8}
          dayMaxEvents={3}
          eventDisplay="block"
          nowIndicator={true}
          selectable={true}
          editable={false}
          // Mobile responsive
          windowResize={(arg) => {
            const calendarApi = arg.view.calendar;
            if (window.innerWidth < 768) {
              calendarApi.changeView('dayGridMonth');
            }
          }}
        />
      </div>

      {/* Legend */}
      <div className="calendar-legend">
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#3b82f6' }}></span>
          <span>Decisions</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#22c55e' }}></span>
          <span>Memos</span>
        </div>
        <div className="legend-item">
          <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
          <span>Tasks</span>
        </div>
      </div>
    </div>
  );
}
