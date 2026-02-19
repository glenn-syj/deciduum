import { useState } from 'react';
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
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  const [addingLogForDecision, setAddingLogForDecision] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    date: new Date().toISOString().split('T')[0],
    status: 'ongoing' as DecisionStatus,
    review_at: '',
    direction_id: '',
  });

  // Log form state
  const [logFormData, setLogFormData] = useState({
    type: 'note' as LogType,
    content: '',
    newStatus: '' as DecisionStatus | '',
  });

  // Fetch logs for a specific decision
  const useLogsForDecision = (decisionId: string) => {
    return useQuery({
      queryKey: ['logs', decisionId],
      queryFn: async () => {
        const response = await decisionsApi.listLogs(decisionId);
        return response.data;
      },
      enabled: !!decisionId,
    });
  };

  const createLogMutation = useMutation({
    mutationFn: ({ decisionId, data }: { decisionId: string; data: NewLogData }) =>
      decisionsApi.createLog(decisionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['logs', variables.decisionId] });
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setAddingLogForDecision(null);
      resetLogForm();
    },
  });

  const resetLogForm = () => {
    setLogFormData({
      type: 'note',
      content: '',
      newStatus: '',
    });
  };

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

  const createMutation = useMutation({
    mutationFn: (data: Partial<Decision>) => decisionsApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setIsCreating(false);
      resetForm();
      // Auto-expand the newly created decision's journey
      if (data.data?.id) {
        setSelectedDecisionId(data.data.id);
      }
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
    if (confirm('Are you sure you want to delete this decision?')) {
      deleteMutation.mutate(id);
    }
  };

  const cancelForm = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
  };

  // Log handlers
  const handleCreateLog = (decisionId: string) => {
    const logData: NewLogData = {
      type: logFormData.type,
      content: logFormData.content,
    };

    // If state_change and new status provided, append to content
    if (logFormData.type === 'state_change' && logFormData.newStatus) {
      logData.content = `Status changed to ${logFormData.newStatus}${logData.content ? ': ' + logData.content : ''}`;
      
      // Also update the decision status
      decisionsApi.update(decisionId, { status: logFormData.newStatus as DecisionStatus });
    }

    createLogMutation.mutate({ decisionId, data: logData });
  };

  const cancelLogForm = () => {
    setAddingLogForDecision(null);
    resetLogForm();
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
  const directions = directionsData?.data || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Decisions</h1>
        {!isCreating && (
          <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
            + New Decision
          </button>
        )}
      </div>

      {isCreating && (
        <div className="card form-card">
          <h2 className="card-title">
            {editingId ? 'Edit Decision' : 'New Decision'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Title</label>
              <input
                type="text"
                className="form-input"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Date</label>
                <input
                  type="date"
                  className="form-input"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Status</label>
                <select
                  className="form-input"
                  value={formData.status}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      status: e.target.value as DecisionStatus,
                    })
                  }
                >
                  <option value="ongoing">Ongoing</option>
                  <option value="completed">Completed</option>
                  <option value="archived">Archived</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Review At (optional)</label>
                <input
                  type="date"
                  className="form-input"
                  value={formData.review_at}
                  onChange={(e) => setFormData({ ...formData, review_at: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Direction</label>
                <select
                  className="form-input"
                  value={formData.direction_id}
                  onChange={(e) =>
                    setFormData({ ...formData, direction_id: e.target.value })
                  }
                >
                  <option value="">None</option>
                  {directions.map((dir) => (
                    <option key={dir.id} value={dir.id}>
                      {dir.title}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-actions">
              <button type="submit" className="btn btn-primary">
                {editingId ? 'Update' : 'Create'}
              </button>
              <button type="button" className="btn btn-secondary" onClick={cancelForm}>
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {decisions.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">⚖️</div>
          <p>No decisions yet. Create your first decision!</p>
        </div>
      ) : (
        <div className="journey-list">
          {decisions.map((decision) => (
            <JourneyCard
              key={decision.id}
              decision={decision}
              isSelected={selectedDecisionId === decision.id}
              onSelect={() => setSelectedDecisionId(selectedDecisionId === decision.id ? null : decision.id)}
              addingLogForDecision={addingLogForDecision}
              onAddLog={() => handleCreateLog(decision.id)}
              onCancelLogForm={cancelLogForm}
              logFormData={logFormData}
              setLogFormData={setLogFormData}
              handleEdit={handleEdit}
              handleDelete={handleDelete}
              useLogsForDecision={useLogsForDecision}
              resetLogForm={resetLogForm}
              setAddingLogForDecision={setAddingLogForDecision}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Journey Card Component with Timeline
interface JourneyCardProps {
  decision: Decision;
  isSelected: boolean;
  onSelect: () => void;
  addingLogForDecision: string | null;
  onAddLog: () => void;
  onCancelLogForm: () => void;
  logFormData: { type: LogType; content: string; newStatus: DecisionStatus | '' };
  setLogFormData: React.Dispatch<React.SetStateAction<{ type: LogType; content: string; newStatus: DecisionStatus | '' }>>;
  handleEdit: (decision: Decision) => void;
  handleDelete: (id: string) => void;
  useLogsForDecision: (decisionId: string) => any;
  resetLogForm: () => void;
  setAddingLogForDecision: (id: string | null) => void;
}

function JourneyCard({
  decision,
  isSelected,
  onSelect,
  addingLogForDecision,
  onAddLog,
  onCancelLogForm,
  logFormData,
  setLogFormData,
  handleEdit,
  handleDelete,
  useLogsForDecision,
  resetLogForm,
  setAddingLogForDecision,
}: JourneyCardProps) {
  const { data: logsData } = useLogsForDecision(decision.id);
  const logs = logsData?.data || [];

  // Sort logs by date (oldest first)
  const sortedLogs = [...logs].sort((a, b) => 
    new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  return (
    <div className="journey-card">
      {/* Header */}
      <div className="journey-header" onClick={onSelect}>
        <div className="journey-title-section">
          <h3 className="journey-title">{decision.title}</h3>
          <span className={`status-badge status-${decision.status}`}>
            {decision.status}
          </span>
        </div>
        <div className="journey-actions">
          <button
            className="btn btn-secondary btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(decision);
            }}
          >
            Edit
          </button>
          <button
            className="btn btn-danger btn-sm"
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(decision.id);
            }}
          >
            Delete
          </button>
        </div>
      </div>

      {/* Timeline Preview */}
      <div className="journey-timeline" onClick={onSelect}>
        {/* Origin Node */}
        <div className="timeline-node origin" title={`Decision made: ${decision.date}`}>
          <span className="node-marker">○</span>
          <span className="node-label">{decision.date}</span>
        </div>

        {/* Timeline Path */}
        <div className="timeline-path">
          {/* Reflection marker if review_at exists */}
          {decision.review_at && (
            <div className="timeline-marker reflection" title={`Review: ${decision.review_at}`}>
              <span className="marker-icon">🌙</span>
            </div>
          )}
          
          {/* Milestone nodes for logs */}
          {sortedLogs.map((log) => (
            <MilestoneNode key={log.id} log={log} />
          ))}
        </div>

        {/* Current Position */}
        <div className={`timeline-node current status-${decision.status}`} title={`Current: ${decision.status}`}>
          <span className="node-marker">
            {decision.status === 'ongoing' ? '●' : decision.status === 'completed' ? '○' : '·'}
          </span>
          <span className="node-label">{decision.status}</span>
        </div>
      </div>

      {/* Expanded Journey View */}
      {isSelected && (
        <div className="journey-expanded">
          {/* Full Timeline with Horizontal Scroll */}
          <div className="journey-scroll">
            <div className="journey-scroll-content">
              {/* Origin */}
              <div className="timeline-item origin">
                <div className="timeline-item-marker">
                  <span className="node-marker">○</span>
                </div>
                <div className="timeline-item-content">
                  <div className="timeline-item-date">{decision.date}</div>
                  <div className="timeline-item-title">Decision made</div>
                  <div className="timeline-item-type">origin</div>
                </div>
              </div>

              {/* Reflection marker */}
              {decision.review_at && (
                <div className="timeline-item reflection">
                  <div className="timeline-item-connector" />
                  <div className="timeline-item-marker">
                    <span className="marker-icon">🌙</span>
                  </div>
                  <div className="timeline-item-content">
                    <div className="timeline-item-date">{decision.review_at}</div>
                    <div className="timeline-item-title">Reflection point</div>
                    <div className="timeline-item-type">review</div>
                  </div>
                </div>
              )}

              {/* Logs as milestones */}
              {sortedLogs.map((log) => (
                <LogTimelineItem key={log.id} log={log} />
              ))}

              {/* Current position */}
              <div className={`timeline-item current status-${decision.status}`}>
                <div className="timeline-item-connector" />
                <div className="timeline-item-marker">
                  <span className="node-marker">
                    {decision.status === 'ongoing' ? '●' : decision.status === 'completed' ? '○' : '·'}
                  </span>
                </div>
                <div className="timeline-item-content">
                  <div className="timeline-item-title">Now</div>
                  <div className="timeline-item-type">{decision.status}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Add Log Form */}
          {addingLogForDecision === decision.id ? (
            <div className="log-form">
              <div className="log-form-row">
                <select
                  className="form-input log-type-select"
                  value={logFormData.type}
                  onChange={(e) => setLogFormData({ ...logFormData, type: e.target.value as LogType })}
                >
                  <option value="note">Note</option>
                  <option value="reflection">Reflection</option>
                  <option value="state_change">Status Change</option>
                </select>
                
                {logFormData.type === 'state_change' && (
                  <select
                    className="form-input status-select"
                    value={logFormData.newStatus}
                    onChange={(e) => setLogFormData({ ...logFormData, newStatus: e.target.value as DecisionStatus | '' })}
                  >
                    <option value="">Select new status</option>
                    <option value="ongoing">Ongoing</option>
                    <option value="completed">Completed</option>
                    <option value="archived">Archived</option>
                  </select>
                )}
              </div>
              
              <textarea
                className="form-textarea log-content"
                placeholder={
                  logFormData.type === 'note' 
                    ? 'Write a note about this decision...' 
                    : logFormData.type === 'reflection'
                    ? 'Reflect on this decision...'
                    : 'Add notes about this status change...'
                }
                value={logFormData.content}
                onChange={(e) => setLogFormData({ ...logFormData, content: e.target.value })}
                rows={3}
              />
              
              <div className="log-form-actions">
                <button 
                  className="btn btn-primary" 
                  onClick={onAddLog}
                  disabled={logFormData.type === 'state_change' && !logFormData.newStatus && !logFormData.content}
                >
                  Add to Journey
                </button>
                <button className="btn btn-secondary" onClick={onCancelLogForm}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              className="btn btn-secondary add-log-btn"
              onClick={() => {
                resetLogForm();
                setAddingLogForDecision(decision.id);
              }}
            >
              + Add to Journey
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Milestone Node (compact view)
function MilestoneNode({ log }: { log: DecisionLog }) {
  const getTypeIcon = () => {
    switch (log.type) {
      case 'reflection': return '💭';
      case 'state_change': return '→';
      default: return '●';
    }
  };

  return (
    <div className={`timeline-mestone type-${log.type}`} title={`${log.type}: ${log.content.slice(0, 50)}...`}>
      <span className="node-marker">{getTypeIcon()}</span>
    </div>
  );
}

// Expanded Timeline Item for Logs
function LogTimelineItem({ log }: { log: DecisionLog }) {
  const [expanded, setExpanded] = useState(false);
  
  const getTypeIcon = () => {
    switch (log.type) {
      case 'reflection': return '💭';
      case 'state_change': return '→';
      default: return '●';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isLongContent = log.content.length > 100;

  return (
    <div className={`timeline-item type-${log.type}`}>
      <div className="timeline-item-connector" />
      <div className="timeline-item-marker">
        <span className="node-marker">{getTypeIcon()}</span>
      </div>
      <div className="timeline-item-content" onClick={() => isLongContent && setExpanded(!expanded)}>
        <div className="timeline-item-date">{formatDate(log.created_at)}</div>
        <div className={`timeline-item-body ${expanded ? 'expanded' : ''}`}>
          {isLongContent && !expanded ? (
            <>
              {log.content.slice(0, 100)}...
              <span className="read-more">tap to read more</span>
            </>
          ) : (
            log.content
          )}
        </div>
        <div className="timeline-item-type">{log.type.replace('_', ' ')}</div>
      </div>
    </div>
  );
}
