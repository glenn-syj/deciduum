import { useMemo, useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { decisionsApi, memosApi, tasksApi, Decision, Memo, Task } from '../utils/api';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';

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
  const [isClient, setIsClient] = useState(false);
  
  // Store ALL FullCalendar modules in state
  const [calendarModules, setCalendarModules] = useState<{
    FullCalendar: typeof import('@fullcalendar/react').default;
    dayGridPlugin: typeof import('@fullcalendar/daygrid').default;
    timeGridPlugin: typeof import('@fullcalendar/timegrid').default;
    interactionPlugin: typeof import('@fullcalendar/interaction').default;
  } | null>(null);
  
  useEffect(() => {
    setIsClient(true);
    
    // Dynamically import ALL FullCalendar modules together
    Promise.all([
      import('@fullcalendar/react'),
      import('@fullcalendar/daygrid'),
      import('@fullcalendar/timegrid'),
      import('@fullcalendar/interaction'),
    ]).then(([FC, dayGrid, timeGrid, interaction]) => {
      setCalendarModules({
        FullCalendar: FC.default,
        dayGridPlugin: dayGrid.default,
        timeGridPlugin: timeGrid.default,
        interactionPlugin: interaction.default,
      });
    }).catch(err => {
      console.error('Failed to load FullCalendar:', err);
    });
  }, []);

  // Only fetch data on client
  const { data: decisionsData, isLoading: decisionsLoading, error: decisionsError } = useQuery({
    queryKey: ['decisions'],
    queryFn: async () => {
      const response = await decisionsApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
    enabled: isClient,
  });

  const { data: memosData, isLoading: memosLoading, error: memosError } = useQuery({
    queryKey: ['memos'],
    queryFn: async () => {
      const response = await memosApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
    enabled: isClient,
  });

  const { data: tasksData, isLoading: tasksLoading, error: tasksError } = useQuery({
    queryKey: ['tasks'],
    queryFn: async () => {
      const response = await tasksApi.list({ limit: 100 });
      return response.data.data;
    },
    staleTime: 5 * 60 * 1000,
    retry: 2,
    enabled: isClient,
  });

  const isLoading = decisionsLoading || memosLoading || tasksLoading;
  const error = decisionsError || memosError || tasksError;

  const events = useMemo<CalendarEvent[]>(() => {
    if (!isClient) return [];
    const calendarEvents: CalendarEvent[] = [];

      decisionsData?.forEach((decision: Decision) => {
      if (decision.date) {
        calendarEvents.push({
          id: `decision-${decision.id}`,
          title: truncateText(decision.title, 50),
          start: decision.date,
          backgroundColor: 'hsl(160 84% 39%)',
          borderColor: 'hsl(160 84% 39%)',
          extendedProps: { type: 'decision', data: decision },
        });
      }
    });

    memosData?.forEach((memo: Memo) => {
      if (memo.date) {
        calendarEvents.push({
          id: `memo-${memo.id}`,
          title: truncateText(memo.content, 50),
          start: memo.date,
          backgroundColor: 'hsl(142.1 76.2% 36.3%)',
          borderColor: 'hsl(142.1 76.2% 36.3%)',
          extendedProps: { type: 'memo', data: memo },
        });
      }
    });

    tasksData?.forEach((task: Task) => {
      if (task.due_date) {
        calendarEvents.push({
          id: `task-${task.id}`,
          title: truncateText(task.title, 50),
          start: task.due_date,
          backgroundColor: 'hsl(24.6 95% 53.1%)',
          borderColor: 'hsl(24.6 95% 53.1%)',
          extendedProps: { type: 'task', data: task },
        });
      }
    });

    return calendarEvents;
  }, [decisionsData, memosData, tasksData, isClient]);

  const handleEventClick = (info: any) => {
    const { type, data } = info.event.extendedProps;
    let message = '';
    if (type === 'decision') {
      message = `Decision: ${data.title}\nStatus: ${data.status}\nDate: ${data.date}`;
    } else if (type === 'memo') {
      message = `Memo: ${data.content}\nDate: ${data.date}`;
    } else if (type === 'task') {
      message = `Task: ${data.title}\nStatus: ${data.status}\nDue: ${data.due_date}`;
    }
    alert(message);
  };

  const getErrorMessage = (err: unknown): string => {
    if (!err) return 'Unknown error';
    if (err instanceof Error) return err.message;
    if (typeof err === 'object' && err !== null && 'message' in err) return String((err as { message: unknown }).message);
    return String(err);
  };

  // Show loading state while modules load
  if (!isClient || !calendarModules) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Calendar</h1>
          <p className="text-sm text-muted-foreground">Loading calendar...</p>
        </div>
        <div className="bg-card border border-border/50 rounded-lg p-4 shadow-sm">
          <Skeleton className="h-[400px] w-full" />
        </div>
      </div>
    );
  }

  const { FullCalendar, dayGridPlugin, timeGridPlugin, interactionPlugin } = calendarModules;

  return (
    <>
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Calendar</h1>
          <p className="text-sm text-muted-foreground">View all your decisions, memos, and tasks</p>
        </div>
        
        {isLoading && (
          <div className="bg-card border border-border/50 rounded-lg p-4 shadow-sm">
            <Skeleton className="h-[400px] w-full" />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <div>
              <p className="text-red-600 font-bold">Failed to load calendar events</p>
              <p className="text-red-600 text-sm">{getErrorMessage(error)}</p>
            </div>
          </div>
        )}
        
        <FullCalendar
          plugins={[
            dayGridPlugin,
            timeGridPlugin,
            interactionPlugin,
          ]}
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
        />

        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'hsl(160 84% 39%)' }}></span>
            <span className="text-muted-foreground">Decisions</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'hsl(142.1 76.2% 36.3%)' }}></span>
            <span className="text-muted-foreground">Memos</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: 'hsl(24.6 95% 53.1%)' }}></span>
            <span className="text-muted-foreground">Tasks</span>
          </div>
        </div>
      </div>
    </>
  );
}
