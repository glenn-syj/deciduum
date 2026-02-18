import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { todayApi, Decision, Memo } from '../utils/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed':
      return 'default';
    case 'ongoing':
      return 'outline';
    case 'archived':
      return 'secondary';
    default:
      return 'outline';
  }
}

export default function Today() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['today'],
    queryFn: async () => {
      const response = await todayApi.get();
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Today</h1>
          <p className="text-sm text-muted-foreground">Loading today's overview...</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-48 bg-muted/50 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Today</h1>
          <p className="text-sm text-muted-foreground">Error loading today's data</p>
        </div>
        <p className="text-destructive">Error loading today's data</p>
      </div>
    );
  }

  const today = data;

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Today</h1>
        <p className="text-sm text-muted-foreground">{today?.date}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="shadow-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Ongoing Decisions</CardTitle>
          </CardHeader>
          <CardContent>
            {today?.ongoing_decisions?.length === 0 ? (
              <p className="text-sm text-muted-foreground">No ongoing decisions</p>
            ) : (
              <ul className="space-y-2">
                {today?.ongoing_decisions?.map((decision: Decision) => (
                  <li key={decision.id}>
                    <Link 
                      to={`/decisions`} 
                      className="flex items-center justify-between p-2 rounded-md hover:bg-muted transition-colors"
                    >
                      <span className="font-medium text-sm">{decision.title}</span>
                      <div className="flex items-center gap-2">
                        <Badge variant={getStatusVariant(decision.status) as any}>
                          {decision.status}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{decision.date}</span>
                      </div>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Today's Decisions</CardTitle>
          </CardHeader>
          <CardContent>
            {today?.todays_decisions?.length === 0 ? (
              <p className="text-sm text-muted-foreground">No decisions made today</p>
            ) : (
              <ul className="space-y-2">
                {today?.todays_decisions?.map((decision: Decision) => (
                  <li key={decision.id}>
                    <Link 
                      to={`/decisions`} 
                      className="flex items-center justify-between p-2 rounded-md hover:bg-muted transition-colors"
                    >
                      <span className="font-medium text-sm">{decision.title}</span>
                      <Badge variant={getStatusVariant(decision.status) as any}>
                        {decision.status}
                      </Badge>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm border-border/50">
          <CardHeader>
            <CardTitle className="text-base">Today's Memos</CardTitle>
          </CardHeader>
          <CardContent>
            {today?.todays_memos?.length === 0 ? (
              <p className="text-sm text-muted-foreground">No memos today</p>
            ) : (
              <ul className="space-y-2">
                {today?.todays_memos?.map((memo: Memo) => (
                  <li key={memo.id}>
                    <Link 
                      to={`/memos`} 
                      className="block p-2 rounded-md hover:bg-muted transition-colors"
                    >
                      <p className="text-sm truncate">{memo.content}</p>
                      <p className="text-xs text-muted-foreground">{memo.date}</p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
