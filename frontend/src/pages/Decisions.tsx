import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decisionsApi, Decision, directionsApi, tasksApi, Task, TaskStatus } from '../utils/api';

export default function Decisions() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [expandedDecisionId, setExpandedDecisionId] = useState<string | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [creatingTaskForDecision, setCreatingTaskForDecision] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    date: new Date().toISOString().split('T')[0],
    status: 'ongoing' as 'completed' | 'ongoing' | 'archived',
    review_at: '',
    direction_id: '',
  });

  // Task form state
  const [taskFormData, setTaskFormData] = useState({
    title: '',
    status: 'pending' as TaskStatus,
    due_date: '',
    notes: '',
  });

  // Fetch tasks for a specific decision
  const useTasksForDecision = (decisionId: string) => {
    return useQuery({
      queryKey: ['tasks', decisionId],
      queryFn: async () => {
        const response = await tasksApi.listByDecision(decisionId);
        return response.data;
      },
      enabled: !!decisionId,
    });
  };

  const createTaskMutation = useMutation({
    mutationFn: ({ decisionId, data }: { decisionId: string; data: { title: string; status?: string; due_date?: string | null; notes?: string | null } }) =>
      tasksApi.createForDecision(decisionId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setCreatingTaskForDecision(null);
      resetTaskForm();
    },
  });

  const updateTaskMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Task> }) =>
      tasksApi.update(id, data),
    onSuccess: () => {
      // Extract decisionId from the task id format or refetch all
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      setEditingTaskId(null);
      resetTaskForm();
    },
  });

  const deleteTaskMutation = useMutation({
    mutationFn: (id: string) => tasksApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  const resetTaskForm = () => {
    setTaskFormData({
      title: '',
      status: 'pending',
      due_date: '',
      notes: '',
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
    if (confirm('Are you sure you want to delete this decision?')) {
      deleteMutation.mutate(id);
    }
  };

  const cancelForm = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
  };

  // Task handlers
  const handleCreateTask = (decisionId: string) => {
    createTaskMutation.mutate({
      decisionId,
      data: {
        title: taskFormData.title,
        status: taskFormData.status,
        due_date: taskFormData.due_date || null,
        notes: taskFormData.notes || null,
      },
    });
  };

  const handleUpdateTask = (task: Task) => {
    updateTaskMutation.mutate({
      id: task.id,
      data: {
        title: taskFormData.title || task.title,
        status: taskFormData.status || task.status,
        due_date: taskFormData.due_date || null,
        notes: taskFormData.notes || null,
      },
    });
  };

  const handleDeleteTask = (taskId: string) => {
    if (confirm('Are you sure you want to delete this task?')) {
      deleteTaskMutation.mutate(taskId);
    }
  };

  const startEditTask = (task: Task) => {
    setEditingTaskId(task.id);
    setTaskFormData({
      title: task.title,
      status: task.status,
      due_date: task.due_date || '',
      notes: task.notes || '',
    });
  };

  const cancelTaskForm = () => {
    setCreatingTaskForDecision(null);
    setEditingTaskId(null);
    resetTaskForm();
  };

  const toggleTasksSection = (decisionId: string) => {
    setExpandedDecisionId(expandedDecisionId === decisionId ? null : decisionId);
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
                      status: e.target.value as 'completed' | 'ongoing' | 'archived',
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
                <label className="form-label">Review At</label>
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
        <div className="list">
          {decisions.map((decision) => (
            <DecisionCard
              key={decision.id}
              decision={decision}
              isExpanded={expandedDecisionId === decision.id}
              onToggleExpand={() => toggleTasksSection(decision.id)}
              editingTaskId={editingTaskId}
              onEditTask={startEditTask}
              creatingTaskForDecision={creatingTaskForDecision}
              onCreateTask={() => handleCreateTask(decision.id)}
              onDeleteTask={handleDeleteTask}
              onUpdateTask={handleUpdateTask}
              onCancelTaskForm={cancelTaskForm}
              taskFormData={taskFormData}
              setTaskFormData={setTaskFormData}
              handleEdit={handleEdit}
              handleDelete={handleDelete}
              useTasksForDecision={useTasksForDecision}
              resetTaskForm={resetTaskForm}
              setCreatingTaskForDecision={setCreatingTaskForDecision}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Decision Card Component with Tasks
interface DecisionCardProps {
  decision: Decision;
  isExpanded: boolean;
  onToggleExpand: () => void;
  editingTaskId: string | null;
  onEditTask: (task: Task) => void;
  creatingTaskForDecision: string | null;
  onCreateTask: () => void;
  onDeleteTask: (taskId: string) => void;
  onUpdateTask: (task: Task) => void;
  onCancelTaskForm: () => void;
  taskFormData: { title: string; status: TaskStatus; due_date: string; notes: string };
  setTaskFormData: React.Dispatch<React.SetStateAction<{ title: string; status: TaskStatus; due_date: string; notes: string }>>;
  handleEdit: (decision: Decision) => void;
  handleDelete: (id: string) => void;
  useTasksForDecision: (decisionId: string) => any;
  resetTaskForm: () => void;
  setCreatingTaskForDecision: (id: string | null) => void;
}

function DecisionCard({
  decision,
  isExpanded,
  onToggleExpand,
  editingTaskId,
  onEditTask,
  creatingTaskForDecision,
  onCreateTask,
  onDeleteTask,
  onUpdateTask,
  onCancelTaskForm,
  taskFormData,
  setTaskFormData,
  handleEdit,
  handleDelete,
  useTasksForDecision,
  resetTaskForm,
  setCreatingTaskForDecision,
}: DecisionCardProps) {
  const { data: tasksData, isLoading: tasksLoading } = useTasksForDecision(decision.id);
  const tasks = tasksData?.data || [];
  const taskCount = tasks.length;

  return (
    <div className="list-item">
      <div className="list-item-content">
        <div className="list-item-title">{decision.title}</div>
        <div className="list-item-meta">
          <span className={`status-badge status-${decision.status}`}>
            {decision.status}
          </span>
          <span>Created: {decision.date}</span>
          {decision.review_at && <span>Review: {decision.review_at}</span>}
          <button
            className="tasks-toggle-btn"
            onClick={onToggleExpand}
          >
            {isExpanded ? '▼' : '▶'} Tasks {taskCount > 0 && `(${taskCount})`}
          </button>
        </div>
      </div>
      <div className="list-item-actions">
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleEdit(decision)}
        >
          Edit
        </button>
        <button
          className="btn btn-danger btn-sm"
          onClick={() => handleDelete(decision.id)}
        >
          Delete
        </button>
      </div>

      {/* Tasks Section */}
      {isExpanded && (
        <div className="tasks-section">
          {tasksLoading ? (
            <div className="loading">Loading tasks...</div>
          ) : tasks.length === 0 ? (
            <div className="empty-text">No tasks yet</div>
          ) : (
            <div className="tasks-list">
              {tasks.map((task: Task) => (
                <TaskItem
                  key={task.id}
                  task={task}
                  isEditing={editingTaskId === task.id}
                  onEdit={() => onEditTask(task)}
                  onDelete={() => onDeleteTask(task.id)}
                  onUpdate={() => onUpdateTask(task)}
                  onCancel={onCancelTaskForm}
                  formData={taskFormData}
                  setFormData={setTaskFormData}
                />
              ))}
            </div>
          )}

          {/* Add Task Form */}
          {creatingTaskForDecision === decision.id ? (
            <div className="task-form">
              <div className="task-form-row">
                <input
                  type="text"
                  className="form-input"
                  placeholder="Task title"
                  value={taskFormData.title}
                  onChange={(e) => setTaskFormData({ ...taskFormData, title: e.target.value })}
                  autoFocus
                />
                <select
                  className="form-input"
                  value={taskFormData.status}
                  onChange={(e) => setTaskFormData({ ...taskFormData, status: e.target.value as TaskStatus })}
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                </select>
                <input
                  type="date"
                  className="form-input"
                  value={taskFormData.due_date}
                  onChange={(e) => setTaskFormData({ ...taskFormData, due_date: e.target.value })}
                />
              </div>
              <div className="task-form-actions">
                <button className="btn btn-primary btn-sm" onClick={onCreateTask}>
                  Add
                </button>
                <button className="btn btn-secondary btn-sm" onClick={onCancelTaskForm}>
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button
              className="btn btn-secondary btn-sm add-task-btn"
              onClick={() => {
                resetTaskForm();
                setCreatingTaskForDecision(decision.id);
              }}
            >
              + Add Task
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Task Item Component
interface TaskItemProps {
  task: Task;
  isEditing: boolean;
  onEdit: () => void;
  onDelete: () => void;
  onUpdate: () => void;
  onCancel: () => void;
  formData: { title: string; status: TaskStatus; due_date: string; notes: string };
  setFormData: React.Dispatch<React.SetStateAction<{ title: string; status: TaskStatus; due_date: string; notes: string }>>;
}

function TaskItem({
  task,
  isEditing,
  onEdit,
  onDelete,
  onUpdate,
  onCancel,
  formData,
  setFormData,
}: TaskItemProps) {
  if (isEditing) {
    return (
      <div className="task-item task-item-editing">
        <div className="task-edit-form">
          <input
            type="text"
            className="form-input"
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Task title"
          />
          <select
            className="form-input"
            value={formData.status}
            onChange={(e) => setFormData({ ...formData, status: e.target.value as TaskStatus })}
          >
            <option value="pending">Pending</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
          <input
            type="date"
            className="form-input"
            value={formData.due_date}
            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
          />
          <div className="task-edit-actions">
            <button className="btn btn-primary btn-sm" onClick={onUpdate}>
              Save
            </button>
            <button className="btn btn-secondary btn-sm" onClick={onCancel}>
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="task-item">
      <div className="task-item-content">
        <span className={`task-status-indicator status-${task.status}`}>
          {task.status === 'completed' ? '☑' : task.status === 'in_progress' ? '◐' : '☐'}
        </span>
        <span className="task-title">{task.title}</span>
        {task.due_date && (
          <span className="task-due-date">due: {task.due_date}</span>
        )}
        <span className={`status-badge status-${task.status === 'completed' ? 'completed' : task.status === 'in_progress' ? 'ongoing' : 'pending'}`}>
          {task.status.replace('_', ' ')}
        </span>
      </div>
      <div className="task-item-actions">
        <button className="btn btn-secondary btn-sm" onClick={onEdit}>
          Edit
        </button>
        <button className="btn btn-danger btn-sm" onClick={onDelete}>
          Delete
        </button>
      </div>
    </div>
  );
}
