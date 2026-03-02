import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { todayApi, decisionsApi, Decision, Memo, DecisionLog } from '../utils/api';

// Utility function to format time ago
function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays === 1) return 'yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return `${Math.floor(diffDays / 30)} months ago`;
}

// Format date for display
function formatLogDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
}

export default function Today() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['today'],
    queryFn: async () => {
      const response = await todayApi.get();
      return response.data;
    },
  });

  // Fetch logs for all ongoing decisions
  const ongoingDecisionIds = data?.ongoing_decisions?.map(d => d.id) || [];
  const { data: logsData } = useQuery({
    queryKey: ['ongoing-decisions-logs', ongoingDecisionIds],
    queryFn: async () => {
      if (ongoingDecisionIds.length === 0) return [];
      
      // Fetch logs for each ongoing decision in parallel
      const logPromises = ongoingDecisionIds.map(async (decisionId) => {
        try {
          const response = await decisionsApi.listLogs(decisionId, { limit: 10 });
          return response.data.data.map(log => ({
            ...log,
            decisionTitle: data?.ongoing_decisions?.find(d => d.id === decisionId)?.title || 'Unknown'
          }));
        } catch {
          return [];
        }
      });
      
      const logsArrays = await Promise.all(logPromises);
      const allLogs = logsArrays.flat();
      
      // Sort by created_at descending and take the most recent 10
      return allLogs
        .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 10);
    },
    enabled: ongoingDecisionIds.length > 0,
  });

  if (isLoading) {
    return (
      <div className="page">
        <div className="terminal-output">
          <div>{`> Loading today's data...`}</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="terminal-output">
          <div>{`> Error: Failed to load today's data`}</div>
        </div>
      </div>
    );
  }

  const today = data;

  return (
    <div className="page">
      <div className="terminal-output">
        <div>{`> Today - ${today?.date}`}</div>
        <div></div>
        <div>{`--- Ongoing Decisions ---`}</div>
        {today?.ongoing_decisions?.length === 0 ? (
          <div>&lt;No ongoing decisions&gt;</div>
        ) : (
          today?.ongoing_decisions?.map((decision: Decision) => (
            <div key={decision.id}>
              {`[${decision.status}] ${decision.title} `}
              <Link to={`/decisions`} className="terminal-link">[view]</Link>
            </div>
          ))
        )}
        <div></div>
        <div>{`--- Today's Decisions ---`}</div>
        {today?.todays_decisions?.length === 0 ? (
          <div>&lt;No decisions made today&gt;</div>
        ) : (
          today?.todays_decisions?.map((decision: Decision) => (
            <div key={decision.id}>
              {`[${decision.status}] ${decision.title} `}
              <Link to={`/decisions`} className="terminal-link">[view]</Link>
            </div>
          ))
        )}
        <div></div>
        <div>{`--- Today's Memos ---`}</div>
        {today?.todays_memos?.length === 0 ? (
          <div>&lt;No memos today&gt;</div>
        ) : (
          today?.todays_memos?.map((memo: Memo) => (
            <div key={memo.id}>
              {`- ${memo.content} `}
              <Link to={`/memos`} className="terminal-link">[view]</Link>
            </div>
          ))
        )}
        <div></div>
        <div>{`--- Recent Activity ---`}</div>
        {!logsData || logsData.length === 0 ? (
          <div>&lt;No recent activity&gt;</div>
        ) : (
          logsData.map((log: DecisionLog & { decisionTitle: string }) => (
            <div key={log.id}>
              {`${formatLogDate(log.created_at)}  ${log.decisionTitle}: ${log.type} - ${log.content.slice(0, 50)}${log.content.length > 50 ? '...' : ''} (${formatTimeAgo(log.created_at)}) `}
              <Link to={`/decisions`} className="terminal-link">[view]</Link>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
