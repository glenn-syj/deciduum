import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decisionsApi, directionsApi, DecisionLog } from '../utils/api';

type LogType = 'note' | 'reflection' | 'state_change';
type DecisionStatus = 'completed' | 'ongoing' | 'archived';

interface Decision {
  id: string;
  title: string;
  date: string;
  status: DecisionStatus;
  review_at: string | null;
  direction_id: string | null;
  created_at: string;
  updated_at: string;
}

interface NewLogData {
  type: LogType;
  content: string;
}

export default function Decisions() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [formData, setFormData] = useState({
    title: '',
    date: new Date().toISOString().split('T')[0],
    status: 'ongoing' as DecisionStatus,
    review_at: '',
    direction_id: '',
  });

  const { data: decisionsData, isLoading } = useQuery({
    queryKey: ['decisions'],
    queryFn: async () => {
      const response = await decisionsApi.list();
      return response.data;
    },
  });

  const { data: directionsData } = useQuery({
    queryKey: ['directions'],
    queryFn: async () => {
      const response = await directionsApi.list({ limit: 100 });
      return response.data;
    },
  });

  const directions = directionsData?.data || [];
  const directionMap = useMemo(() => {
    const map: Record<string, string> = {};
    directions.forEach(dir => {
      map[dir.id] = dir.title;
    });
    return map;
  }, [directions]);

  const createMutation = useMutation({
    mutationFn: (data: Partial<Decision>) => decisionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setIsCreating(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Decision> }) =>
      decisionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setEditingId(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => decisionsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
    },
  });

  const resetForm = () => {
    setFormData({
      title: '',
      date: new Date().toISOString().split('T')[0],
      status: 'ongoing',
      review_at: '',
      direction_id: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData: Partial<Decision> = {
      title: formData.title,
      date: formData.date,
      status: formData.status,
      review_at: formData.review_at || null,
      direction_id: formData.direction_id || null,
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleEdit = (decision: Decision) => {
    setEditingId(decision.id);
    setFormData({
      title: decision.title,
      date: decision.date,
      status: decision.status,
      review_at: decision.review_at || '',
      direction_id: decision.direction_id || '',
    });
    setIsCreating(true);
  };

  const handleDelete = (id: string) => {
    if (confirm('Delete this decision? This cannot be undone.')) {
      deleteMutation.mutate(id);
    }
  };

  const cancelForm = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
  };

  const toggleExpanded = (id: string) => {
    setExpandedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Decisions</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  const decisions = decisionsData?.data || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Decisions</h1>
      </div>

      {isCreating && (
        <div className="form-section">
          <h3>{editingId ? '> Edit Decision' : '> New Decision'}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Title: </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Date: </label>
                <input
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Status: </label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as DecisionStatus })}
                >
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Review at: </label>
                <input
                  type="date"
                  value={formData.review_at}
                  onChange={(e) => setFormData({ ...formData, review_at: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Direction: </label>
                <select
                  value={formData.direction_id}
                  onChange={(e) => setFormData({ ...formData, direction_id: e.target.value })}
                >
                  <option value="">None</option>
                  {directions.map(dir => (
                    <option key={dir.id} value={dir.id}>{dir.title}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit">{editingId ? '[save]' : '[create]'}</button>
              <button type="button" onClick={cancelForm}>[cancel]</button>
            </div>
          </form>
        </div>
      )}

      {!isCreating && (
        <button className="btn-link" onClick={() => setIsCreating(true)}>+ new</button>
      )}

      {decisions.length === 0 ? (
        <div className="empty-state">
          <p>No decisions yet.</p>
        </div>
      ) : (
        <div className="decisions-list">
          {decisions.map((decision) => (
            <DecisionItem
              key={decision.id}
              decision={decision}
              directionTitle={decision.direction_id ? directionMap[decision.direction_id] : null}
              isExpanded={expandedIds.has(decision.id)}
              onToggle={() => toggleExpanded(decision.id)}
              onEdit={() => handleEdit(decision)}
              onDelete={() => handleDelete(decision.id)}
              directions={directions}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface DecisionItemProps {
  decision: Decision;
  directionTitle: string | null;
  isExpanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
  directions: { id: string; title: string }[];
}

function DecisionItem({
  decision,
  directionTitle,
  isExpanded,
  onToggle,
  onEdit,
  onDelete,
  directions: _directions,
}: DecisionItemProps) {
  const queryClient = useQueryClient();
  const [addingLog, setAddingLog] = useState(false);
  const [logFormData, setLogFormData] = useState({
    type: 'note' as LogType,
    content: '',
  });

  const { data: logsData } = useQuery({
    queryKey: ['logs', decision.id],
    queryFn: async () => {
      const response = await decisionsApi.listLogs(decision.id);
      return response.data;
    },
    enabled: !!decision.id,
  });
  const logs: DecisionLog[] = logsData?.data || [];

  const createLogMutation = useMutation({
    mutationFn: ({ decisionId, data }: { decisionId: string; data: NewLogData }) =>
      decisionsApi.createLog(decisionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['logs', variables.decisionId] });
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setAddingLog(false);
      setLogFormData({ type: 'note', content: '' });
    },
  });

  const updateDecisionStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: DecisionStatus }) =>
      decisionsApi.update(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
    },
  });

  const handleCreateLog = () => {
    if (!logFormData.content.trim()) return;
    const logData: NewLogData = {
      type: logFormData.type,
      content: logFormData.content,
    };
    createLogMutation.mutate({ decisionId: decision.id, data: logData });
  };

  const handleStatusChange = (newStatus: DecisionStatus) => {
    updateDecisionStatusMutation.mutate({ id: decision.id, status: newStatus });
  };

  const cancelLogForm = () => {
    setAddingLog(false);
    setLogFormData({ type: 'note', content: '' });
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="decision-item">
      {/* Main decision line */}
      <div className="decision-main">
        <span>[{decision.status}] </span>
        <span>{formatDate(decision.date)}: </span>
        <span>{decision.title}</span>
        {directionTitle && <span> ({directionTitle})</span>}
        <span> </span>
        <button className="btn-link" onClick={onToggle}>
          {isExpanded ? '[-]' : '[+]'}
        </button>
      </div>

      {/* Expanded content with logs */}
      {isExpanded && (
        <div className="decision-expanded">
          {/* Action links */}
          <div className="decision-actions">
            <button className="btn-link" onClick={onEdit}>[edit]</button>
            <button className="btn-link" onClick={onDelete}>[delete]</button>
            <select
              value={decision.status}
              onChange={(e) => handleStatusChange(e.target.value as DecisionStatus)}
              className="status-select"
            >
              <option value="ongoing">ongoing</option>
              <option value="completed">completed</option>
              <option value="archived">archived</option>
            </select>
          </div>

          {/* Decision Journey Timeline */}
          {logs.length > 0 && (
            <div className="decision-journey">
              <div className="journey-section-header">--- Journey ---</div>
              {(() => {
                // Build timeline entries
                const entries: { date: string; dateStr: string; type: string; content: string; isReview?: boolean }[] = [];
                
                // Add origin entry (the decision date)
                entries.push({
                  date: decision.date,
                  dateStr: formatDate(decision.date),
                  type: 'origin',
                  content: 'Decision made',
                });
                
                // Add log entries sorted by date
                const sortedLogs = [...logs].sort((a, b) => 
                  new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
                );
                sortedLogs.forEach(log => {
                  entries.push({
                    date: log.created_at,
                    dateStr: formatDate(log.created_at),
                    type: log.type,
                    content: log.content,
                  });
                });
                
                // Add review point if exists
                if (decision.review_at) {
                  entries.push({
                    date: decision.review_at,
                    dateStr: formatDate(decision.review_at),
                    type: 'review',
                    content: `Reflection point (review_at)`,
                    isReview: true,
                  });
                }
                
                // Sort all entries chronologically
                entries.sort((a, b) => 
                  new Date(a.date).getTime() - new Date(b.date).getTime()
                );
                
                return (
                  <>
                    {entries.map((entry, idx) => (
                      <div key={idx} className={`journey-entry ${entry.isReview ? 'journey-review' : ''}`}>
                        {entry.type === 'origin' ? (
                          <span className="journey-date">{entry.dateStr}</span>
                        ) : (
                          <span className="journey-date">{entry.dateStr}</span>
                        )}
                        <span className={`journey-type journey-${entry.type}`}>
                          {entry.type.padEnd(11)}
                        </span>
                        <span className="journey-content">{entry.content}</span>
                      </div>
                    ))}
                    {/* Current position */}
                    <div className="journey-entry journey-current">
                      <span className="journey-date">            </span>
                      <span className="journey-marker">{`>>> ${decision.status}`}</span>
                    </div>
                  </>
                );
              })()}
            </div>
          )}

          {/* Add log form */}
          {addingLog ? (
            <div className="log-form">
              <div className="log-form-row">
                <select
                  value={logFormData.type}
                  onChange={(e) => setLogFormData({ ...logFormData, type: e.target.value as LogType })}
                >
                  <option value="note">note</option>
                  <option value="reflection">reflection</option>
                </select>
              </div>
              <textarea
                placeholder={logFormData.type === 'note' ? 'Write a note...' : 'Reflect on this decision...'}
                value={logFormData.content}
                onChange={(e) => setLogFormData({ ...logFormData, content: e.target.value })}
                rows={2}
              />
              <div className="log-form-actions">
                <button onClick={handleCreateLog} disabled={!logFormData.content.trim()}>
                  [save]
                </button>
                <button onClick={cancelLogForm}>[cancel]</button>
              </div>
            </div>
          ) : (
            <button className="btn-link" onClick={() => setAddingLog(true)}>
              + add log
            </button>
          )}
        </div>
      )}
    </div>
  );
}
