import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { todayApi, Decision, Memo } from '../utils/api';

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
      </div>
    </div>
  );
}
