import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Select from '@radix-ui/react-select';
import * as Dialog from '@radix-ui/react-dialog';
import * as DropdownMenu from '@radix-ui/react-dropdown-menu';
import { decisionsApi, directionsApi, DecisionLog, memosApi, tasksApi, Memo, Task } from '../utils/api';

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

type TimelineItemType = 'origin' | 'review' | 'log' | 'task' | 'memo';

interface TimelineItem {
  id: string;
  type: TimelineItemType;
  date: string;
  title: string;
  content?: string;
  status?: string;
  logType?: string;
}

function StatusSelect({ 
  value, 
  onValueChange,
  className = '' 
}: { 
  value: string; 
  onValueChange: (value: string) => void;
  className?: string;
}) {
  return (
    <Select.Root value={value} onValueChange={onValueChange}>
      <Select.Trigger className={`select-trigger ${className}`}>
        <Select.Value />
        <Select.Icon className="select-icon">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="select-content" position="popper" sideOffset={4}>
          <Select.Viewport className="select-viewport">
            <Select.Item value="ongoing" className="select-item">
              <Select.ItemText>Ongoing</Select.ItemText>
              <Select.ItemIndicator className="select-item-indicator">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Select.ItemIndicator>
            </Select.Item>
            <Select.Item value="completed" className="select-item">
              <Select.ItemText>Completed</Select.ItemText>
              <Select.ItemIndicator className="select-item-indicator">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Select.ItemIndicator>
            </Select.Item>
            <Select.Item value="archived" className="select-item">
              <Select.ItemText>Archived</Select.ItemText>
              <Select.ItemIndicator className="select-item-indicator">
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </Select.ItemIndicator>
            </Select.Item>
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

function DirectionSelect({ 
  value, 
  onValueChange,
  directions,
  className = '' 
}: { 
  value: string; 
  onValueChange: (value: string) => void;
  directions: { id: string; title: string }[];
  className?: string;
}) {
  return (
    <Select.Root value={value || 'none'} onValueChange={(v) => onValueChange(v === 'none' ? '' : v)}>
      <Select.Trigger className={`select-trigger ${className}`}>
        <Select.Value placeholder="Select direction..." />
        <Select.Icon className="select-icon">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="select-content" position="popper" sideOffset={4}>
          <Select.Viewport className="select-viewport">
            <Select.Item value="none" className="select-item">
              <Select.ItemText>None</Select.ItemText>
            </Select.Item>
            {directions.map((dir) => (
              <Select.Item key={dir.id} value={dir.id} className="select-item">
                <Select.ItemText>{dir.title}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

function DeleteDialog({ 
  open, 
  onOpenChange, 
  onConfirm 
}: { 
  open: boolean; 
  onOpenChange: (open: boolean) => void; 
  onConfirm: () => void;
}) {
  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="dialog-overlay" />
        <Dialog.Content className="dialog-content">
          <Dialog.Title className="dialog-title">Delete Decision</Dialog.Title>
          <Dialog.Description className="dialog-description">
            Are you sure you want to delete this decision? This action cannot be undone.
          </Dialog.Description>
          <div className="flex gap-3 justify-end">
            <Dialog.Close asChild>
              <button className="btn btn-secondary">Cancel</button>
            </Dialog.Close>
            <button className="btn btn-danger" onClick={onConfirm}>
              Delete
            </button>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}

const getTypeIcon = (type: string, status?: string, logType?: string): string => {
  if (type === 'memo') return '📝';
  if (type === 'task') return status === 'completed' ? '✓' : '☐';
  if (type === 'log') {
    if (logType === 'reflection') return '💭';
    if (logType === 'state_change') return '→';
  }
  return '●';
};

export default function Decisions() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
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

  const createMutation = useMutation({
    mutationFn: (data: Partial<Decision>) => decisionsApi.create(data),
    onSuccess: (response: any) => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setIsCreating(false);
      resetForm();
      if (response.data?.id) {
        setSelectedDecisionId(response.data.id);
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

  const handleDeleteClick = (id: string) => {
    setDeletingId(id);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = () => {
    if (deletingId) {
      deleteMutation.mutate(deletingId);
      setDeleteDialogOpen(false);
      setDeletingId(null);
    }
  };

  const cancelForm = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
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
  const directionMap = useMemo(() => {
    const map: Record<string, string> = {};
    directions.forEach(dir => {
      map[dir.id] = dir.title;
    });
    return map;
  }, [directions]);

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
                <StatusSelect
                  value={formData.status}
                  onValueChange={(value) => setFormData({ ...formData, status: value as DecisionStatus })}
                />
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
                <DirectionSelect
                  value={formData.direction_id}
                  onValueChange={(value) => setFormData({ ...formData, direction_id: value })}
                  directions={directions}
                />
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
              directionTitle={decision.direction_id ? directionMap[decision.direction_id] : null}
              isSelected={selectedDecisionId === decision.id}
              onSelect={() => setSelectedDecisionId(selectedDecisionId === decision.id ? null : decision.id)}
              handleEdit={handleEdit}
              handleDelete={handleDeleteClick}
              directions={directions}
            />
          ))}
        </div>
      )}

      <DeleteDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}

interface JourneyCardProps {
  decision: Decision;
  directionTitle: string | null;
  isSelected: boolean;
  onSelect: () => void;
  handleEdit: (decision: Decision) => void;
  handleDelete: (id: string) => void;
  directions: { id: string; title: string }[];
}

function JourneyCard({
  decision,
  directionTitle,
  isSelected,
  onSelect,
  handleEdit,
  handleDelete,
  directions: _directions,
}: JourneyCardProps) {
  const queryClient = useQueryClient();
  const [addingLogForDecision, setAddingLogForDecision] = useState(false);
  const [addingTask, setAddingTask] = useState(false);
  const [addingMemo, setAddingMemo] = useState(false);
  const [logFormData, setLogFormData] = useState({
    type: 'note' as LogType,
    content: '',
    newStatus: '' as DecisionStatus | '',
  });
  const [taskFormData, setTaskFormData] = useState({ title: '', notes: '' });
  const [memoFormData, setMemoFormData] = useState({ content: '' });

  const { data: logsData } = useQuery({
    queryKey: ['logs', decision.id],
    queryFn: async () => {
      const response = await decisionsApi.listLogs(decision.id);
      return response.data;
    },
    enabled: !!decision.id,
  });
  const logs: DecisionLog[] = logsData?.data || [];

  const { data: tasksData } = useQuery<{ data: Task[] }>({
    queryKey: ['tasks', decision.id],
    queryFn: async () => {
      const response = await tasksApi.listByDecision(decision.id);
      return response.data;
    },
    enabled: !!decision.id,
  });

  const { data: memosData } = useQuery<{ data: Memo[] }>({
    queryKey: ['memos', decision.id],
    queryFn: async () => {
      const response = await memosApi.listByDecision(decision.id);
      return response.data;
    },
    enabled: !!decision.id,
  });

  const createLogMutation = useMutation({
    mutationFn: ({ decisionId, data }: { decisionId: string; data: NewLogData }) =>
      decisionsApi.createLog(decisionId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['logs', variables.decisionId] });
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
      setAddingLogForDecision(false);
      setLogFormData({ type: 'note', content: '', newStatus: '' });
    },
  });

  const createTaskMutation = useMutation({
    mutationFn: (data: { decision_id: string; title: string; notes?: string }) =>
      tasksApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks', decision.id] });
      setAddingTask(false);
      setTaskFormData({ title: '', notes: '' });
    },
  });

  const createMemoMutation = useMutation({
    mutationFn: (data: { decision_id: string; content: string }) =>
      memosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos', decision.id] });
      setAddingMemo(false);
      setMemoFormData({ content: '' });
    },
  });

  const updateDecisionStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: DecisionStatus }) =>
      decisionsApi.update(id, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['decisions'] });
    },
  });

  const timelineItems = useMemo(() => {
    const items: TimelineItem[] = [];
    
    items.push({
      id: `origin-${decision.id}`,
      type: 'origin',
      date: decision.date,
      title: 'Decision made',
    });
    
    if (decision.review_at) {
      items.push({
        id: `review-${decision.id}`,
        type: 'review',
        date: decision.review_at,
        title: 'Reflection point',
      });
    }
    
    logs.forEach(log => {
      items.push({
        id: log.id,
        type: 'log',
        date: log.created_at,
        title: log.type === 'state_change' ? 'Status changed' : log.type.charAt(0).toUpperCase() + log.type.slice(1),
        content: log.content,
        logType: log.type,
      });
    });
    
    (tasksData?.data || []).forEach(task => {
      items.push({
        id: task.id,
        type: 'task',
        date: task.created_at,
        title: task.title,
        content: task.notes || undefined,
        status: task.status,
      });
    });
    
    (memosData?.data || []).forEach(memo => {
      items.push({
        id: memo.id,
        type: 'memo',
        date: memo.created_at,
        title: 'Memo',
        content: memo.content,
      });
    });
    
    return items.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [decision.id, decision.date, decision.review_at, logs, tasksData?.data, memosData?.data]);

  const handleCreateLog = () => {
    const logData: NewLogData = {
      type: logFormData.type,
      content: logFormData.content,
    };

    if (logFormData.type === 'state_change' && logFormData.newStatus) {
      logData.content = `Status changed to ${logFormData.newStatus}${logData.content ? ': ' + logFormData.content : ''}`;
      updateDecisionStatusMutation.mutate({ id: decision.id, status: logFormData.newStatus as DecisionStatus });
    }

    createLogMutation.mutate({ decisionId: decision.id, data: logData });
  };

  const handleCreateTask = () => {
    if (!taskFormData.title.trim()) return;
    createTaskMutation.mutate({
      decision_id: decision.id,
      title: taskFormData.title,
      notes: taskFormData.notes || undefined,
    });
  };

  const handleCreateMemo = () => {
    if (!memoFormData.content.trim()) return;
    createMemoMutation.mutate({
      decision_id: decision.id,
      content: memoFormData.content,
    });
  };

  const handleStatusChange = (newStatus: DecisionStatus) => {
    updateDecisionStatusMutation.mutate({ id: decision.id, status: newStatus });
  };

  const cancelLogForm = () => {
    setAddingLogForDecision(false);
    setLogFormData({ type: 'note', content: '', newStatus: '' });
  };

  const cancelTaskForm = () => {
    setAddingTask(false);
    setTaskFormData({ title: '', notes: '' });
  };

  const cancelMemoForm = () => {
    setAddingMemo(false);
    setMemoFormData({ content: '' });
  };

  return (
    <div className="journey-card">
      <div className="journey-header" onClick={onSelect}>
        <div className="journey-title-section">
          <h3 className="journey-title">{decision.title}</h3>
          <div className="journey-meta">
            <span className={`status-badge status-${decision.status}`}>
              {decision.status}
            </span>
            {directionTitle && (
              <span className="direction-badge">{directionTitle}</span>
            )}
          </div>
        </div>
        <div className="journey-actions">
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button
                className="btn btn-secondary btn-sm"
                onClick={(e) => e.stopPropagation()}
              >
                Actions
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content className="dropdown-content" sideOffset={5}>
                <DropdownMenu.Item 
                  className="dropdown-item"
                  onSelect={() => handleEdit(decision)}
                >
                  Edit Decision
                </DropdownMenu.Item>
                <DropdownMenu.Sub>
                  <DropdownMenu.SubTrigger className="dropdown-item">
                    Change Status
                  </DropdownMenu.SubTrigger>
                  <DropdownMenu.Portal>
                    <DropdownMenu.SubContent className="dropdown-content">
                      <DropdownMenu.Item 
                        className="dropdown-item"
                        onSelect={() => handleStatusChange('ongoing')}
                      >
                        Ongoing
                      </DropdownMenu.Item>
                      <DropdownMenu.Item 
                        className="dropdown-item"
                        onSelect={() => handleStatusChange('completed')}
                      >
                        Completed
                      </DropdownMenu.Item>
                      <DropdownMenu.Item 
                        className="dropdown-item"
                        onSelect={() => handleStatusChange('archived')}
                      >
                        Archived
                      </DropdownMenu.Item>
                    </DropdownMenu.SubContent>
                  </DropdownMenu.Portal>
                </DropdownMenu.Sub>
                <DropdownMenu.Separator className="dropdown-separator" />
                <DropdownMenu.Item 
                  className="dropdown-item danger"
                  onSelect={() => handleDelete(decision.id)}
                >
                  Delete
                </DropdownMenu.Item>
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>
      </div>

      <div className="journey-timeline" onClick={onSelect}>
        <div className="timeline-node origin" title={`Decision made: ${decision.date}`}>
          <span className="node-marker">○</span>
          <span className="node-label">{decision.date}</span>
        </div>

        <div className="timeline-path">
          {decision.review_at && (
            <div className="timeline-marker reflection" title={`Review: ${decision.review_at}`}>
              <span className="marker-icon">🌙</span>
            </div>
          )}
          
          {timelineItems.filter(item => item.type !== 'origin' && item.type !== 'review').map((item) => (
            <MilestoneNode key={item.id} item={item} />
          ))}
        </div>

        <div className={`timeline-node current status-${decision.status}`} title={`Current: ${decision.status}`}>
          <span className="node-marker">
            {decision.status === 'ongoing' ? '●' : decision.status === 'completed' ? '○' : '·'}
          </span>
          <span className="node-label">{decision.status}</span>
        </div>
      </div>

      {isSelected && (
        <div className="journey-expanded">
          <div className="journey-scroll">
            <div className="journey-scroll-content">
              {timelineItems.filter(item => item.type === 'origin' || item.type === 'review').map((item) => (
                <div key={item.id} className={`timeline-item ${item.type}`}>
                  <div className="timeline-item-marker">
                    {item.type === 'origin' ? (
                      <span className="node-marker">○</span>
                    ) : (
                      <span className="marker-icon">🌙</span>
                    )}
                  </div>
                  <div className="timeline-item-content">
                    <div className="timeline-item-date">{item.date}</div>
                    <div className="timeline-item-title">{item.title}</div>
                    <div className="timeline-item-type">{item.type}</div>
                  </div>
                </div>
              ))}

              {timelineItems.filter(item => item.type === 'log' || item.type === 'task' || item.type === 'memo').map((item, index, arr) => {
                const prevItem = index > 0 ? arr[index - 1] : null;
                const needsConnector = !prevItem || prevItem.type === 'origin' || prevItem.type === 'review';
                return (
                  <TimelineItemComponent 
                    key={item.id} 
                    item={item} 
                    needsConnector={needsConnector}
                  />
                );
              })}

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

          {addingLogForDecision ? (
            <div className="log-form">
              <div className="log-form-row">
                <LogTypeSelect
                  value={logFormData.type}
                  onValueChange={(value) => setLogFormData({ ...logFormData, type: value as LogType })}
                  className="log-type-select"
                />
                
                {logFormData.type === 'state_change' && (
                  <StatusSelect
                    value={logFormData.newStatus as string}
                    onValueChange={(value) => setLogFormData({ ...logFormData, newStatus: value as DecisionStatus | '' })}
                    className="status-select"
                  />
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
                  onClick={handleCreateLog}
                  disabled={logFormData.type === 'state_change' && !logFormData.newStatus && !logFormData.content}
                >
                  Add to Journey
                </button>
                <button className="btn btn-secondary" onClick={cancelLogForm}>
                  Cancel
                </button>
              </div>
            </div>
          ) : addingTask ? (
            <div className="log-form">
              <input
                type="text"
                className="form-input"
                placeholder="Task title..."
                value={taskFormData.title}
                onChange={(e) => setTaskFormData({ ...taskFormData, title: e.target.value })}
              />
              <textarea
                className="form-textarea"
                placeholder="Notes (optional)..."
                value={taskFormData.notes}
                onChange={(e) => setTaskFormData({ ...taskFormData, notes: e.target.value })}
                rows={2}
              />
              <div className="log-form-actions">
                <button 
                  className="btn btn-primary" 
                  onClick={handleCreateTask}
                  disabled={!taskFormData.title.trim()}
                >
                  Add Task
                </button>
                <button className="btn btn-secondary" onClick={cancelTaskForm}>
                  Cancel
                </button>
              </div>
            </div>
          ) : addingMemo ? (
            <div className="log-form">
              <textarea
                className="form-textarea"
                placeholder="Write your memo..."
                value={memoFormData.content}
                onChange={(e) => setMemoFormData({ ...memoFormData, content: e.target.value })}
                rows={3}
              />
              <div className="log-form-actions">
                <button 
                  className="btn btn-primary" 
                  onClick={handleCreateMemo}
                  disabled={!memoFormData.content.trim()}
                >
                  Add Memo
                </button>
                <button className="btn btn-secondary" onClick={cancelMemoForm}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <div className="add-actions-row">
              <button
                className="btn btn-secondary add-log-btn"
                onClick={() => setAddingLogForDecision(true)}
              >
                + Add Log
              </button>
              <button
                className="btn btn-secondary add-log-btn"
                onClick={() => setAddingTask(true)}
              >
                + Add Task
              </button>
              <button
                className="btn btn-secondary add-log-btn"
                onClick={() => setAddingMemo(true)}
              >
                + Add Memo
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function LogTypeSelect({
  value,
  onValueChange,
  className = ''
}: {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
}) {
  return (
    <Select.Root value={value} onValueChange={onValueChange}>
      <Select.Trigger className={`select-trigger ${className}`}>
        <Select.Value />
        <Select.Icon className="select-icon">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </Select.Icon>
      </Select.Trigger>
      <Select.Portal>
        <Select.Content className="select-content" position="popper" sideOffset={4}>
          <Select.Viewport className="select-viewport">
            <Select.Item value="note" className="select-item">
              <Select.ItemText>Note</Select.ItemText>
            </Select.Item>
            <Select.Item value="reflection" className="select-item">
              <Select.ItemText>Reflection</Select.ItemText>
            </Select.Item>
            <Select.Item value="state_change" className="select-item">
              <Select.ItemText>Status Change</Select.ItemText>
            </Select.Item>
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

function MilestoneNode({ item }: { item: TimelineItem }) {
  const icon = useMemo(
    () => getTypeIcon(item.type, item.status, item.logType),
    [item.type, item.status, item.logType]
  );

  return (
    <div className={`timeline-mestone type-${item.type}`} title={`${item.title}: ${item.content?.slice(0, 50) || ''}...`}>
      <span className="node-marker">{icon}</span>
    </div>
  );
}

function TimelineItemComponent({ item, needsConnector }: { item: TimelineItem; needsConnector?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  
  const icon = useMemo(
    () => getTypeIcon(item.type, item.status, item.logType),
    [item.type, item.status, item.logType]
  );

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isLongContent = item.content ? item.content.length > 100 : false;

  return (
    <div className={`timeline-item type-${item.type}`}>
      {needsConnector && <div className="timeline-item-connector" />}
      <div className="timeline-item-marker">
        <span className="node-marker">{icon}</span>
      </div>
      <div className="timeline-item-content" onClick={() => isLongContent && setExpanded(!expanded)}>
        <div className="timeline-item-date">{formatDate(item.date)}</div>
        <div className="timeline-item-title">{item.title}</div>
        {item.content && (
          <div className={`timeline-item-body ${expanded ? 'expanded' : ''}`}>
            {isLongContent && !expanded ? (
              <>
                {item.content.slice(0, 100)}...
                <span className="read-more">tap to read more</span>
              </>
            ) : (
              item.content
            )}
          </div>
        )}
        <div className="timeline-item-type">{item.type}</div>
      </div>
    </div>
  );
}
