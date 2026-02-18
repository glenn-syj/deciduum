import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { todayApi } from '../utils/api';

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
        <div className="page-header">
          <h1>Today</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Today</h1>
        </div>
        <div className="error">Error loading today's data</div>
      </div>
    );
  }

  const today = data?.data;

  return (
    <div className="page">
      <div className="page-header">
        <h1>Today - {today?.date}</h1>
      </div>

      <div className="today-grid">
        <section className="card">
          <h2 className="card-title">Ongoing Decisions</h2>
          {today?.ongoing_decisions.length === 0 ? (
            <p className="empty-text">No ongoing decisions</p>
          ) : (
            <ul className="today-list">
              {today?.ongoing_decisions.map((decision) => (
                <li key={decision.id} className="today-list-item">
                  <Link to={`/decisions`} className="today-list-link">
                    <span className="today-list-title">{decision.title}</span>
                    <span className="today-list-meta">
                      <span className={`status-badge status-${decision.status}`}>
                        {decision.status}
                      </span>
                      {decision.date}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2 className="card-title">Today's Decisions</h2>
          {today?.todays_decisions.length === 0 ? (
            <p className="empty-text">No decisions made today</p>
          ) : (
            <ul className="today-list">
              {today?.todays_decisions.map((decision) => (
                <li key={decision.id} className="today-list-item">
                  <Link to={`/decisions`} className="today-list-link">
                    <span className="today-list-title">{decision.title}</span>
                    <span className="today-list-meta">
                      <span className={`status-badge status-${decision.status}`}>
                        {decision.status}
                      </span>
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2 className="card-title">Today's Memos</h2>
          {today?.todays_memos.length === 0 ? (
            <p className="empty-text">No memos today</p>
          ) : (
            <ul className="today-list">
              {today?.todays_memos.map((memo) => (
                <li key={memo.id} className="today-list-item">
                  <Link to={`/memos`} className="today-list-link">
                    <span className="today-list-content">{memo.content}</span>
                    <span className="today-list-meta">{memo.date}</span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
