import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decisionsApi, Decision, directionsApi, tasksApi, Task, TaskStatus } from '../utils/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Plus, Pencil, Trash2, ChevronDown, ChevronRight, Check } from 'lucide-react';

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed':
      return 'default';
    case 'ongoing':
      return 'outline';
    case 'archived':
      return 'secondary';
    case 'in_progress':
      return 'outline';
    case 'pending':
      return 'secondary';
    default:
      return 'outline';
  }
}

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

  const [taskFormData, setTaskFormData] = useState({
    title: '',
    status: 'pending' as TaskStatus,
    due_date: '',
    notes: '',
  });

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
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Decisions</h1>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  const decisions = decisionsData?.data || [];
  const directions = directionsData?.data || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Decisions</h1>
        {!isCreating && (
          <Button onClick={() => setIsCreating(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Decision
          </Button>
        )}
      </div>

      {isCreating && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Decision' : 'New Decision'}</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date">Date</Label>
                  <Input
                    id="date"
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="status">Status</Label>
                  <Select
                    value={formData.status}
                    onValueChange={(value) => setFormData({ ...formData, status: value as 'completed' | 'ongoing' | 'archived' })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ongoing">Ongoing</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                      <SelectItem value="archived">Archived</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="review_at">Review At</Label>
                  <Input
                    id="review_at"
                    type="date"
                    value={formData.review_at}
                    onChange={(e) => setFormData({ ...formData, review_at: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="direction">Direction</Label>
                  <Select
                    value={formData.direction_id}
                    onValueChange={(value) => setFormData({ ...formData, direction_id: value })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select direction" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="">None</SelectItem>
                      {directions.map((dir) => (
                        <SelectItem key={dir.id} value={dir.id}>
                          {dir.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="flex gap-2">
                <Button type="submit">
                  {editingId ? 'Update' : 'Create'}
                </Button>
                <Button type="button" variant="outline" onClick={cancelForm}>
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {decisions.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">No decisions yet. Create your first decision!</p>
        </div>
      ) : (
        <div className="space-y-4">
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
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-lg">{decision.title}</h3>
              <Badge variant={getStatusVariant(decision.status) as any}>
                {decision.status}
              </Badge>
            </div>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>Created: {decision.date}</span>
              {decision.review_at && <span>Review: {decision.review_at}</span>}
              <Button
                variant="ghost"
                size="sm"
                onClick={onToggleExpand}
              >
                {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                Tasks {taskCount > 0 && `(${taskCount})`}
              </Button>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => handleEdit(decision)}>
              <Pencil className="h-4 w-4" />
            </Button>
            <Button variant="destructive" size="sm" onClick={() => handleDelete(decision.id)}>
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {isExpanded && (
          <div className="mt-4 pt-4 border-t">
            <Separator className="mb-4" />
            {tasksLoading ? (
              <p className="text-muted-foreground">Loading tasks...</p>
            ) : tasks.length === 0 ? (
              <p className="text-muted-foreground text-sm">No tasks yet</p>
            ) : (
              <div className="space-y-2 mb-4">
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

            {creatingTaskForDecision === decision.id ? (
              <div className="space-y-2 p-3 bg-muted/50 rounded-md">
                <div className="flex gap-2 flex-wrap">
                  <Input
                    placeholder="Task title"
                    value={taskFormData.title}
                    onChange={(e) => setTaskFormData({ ...taskFormData, title: e.target.value })}
                    className="flex-1"
                    autoFocus
                  />
                  <Select
                    value={taskFormData.status}
                    onValueChange={(value) => setTaskFormData({ ...taskFormData, status: value as TaskStatus })}
                  >
                    <SelectTrigger className="w-[130px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="pending">Pending</SelectItem>
                      <SelectItem value="in_progress">In Progress</SelectItem>
                      <SelectItem value="completed">Completed</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input
                    type="date"
                    value={taskFormData.due_date}
                    onChange={(e) => setTaskFormData({ ...taskFormData, due_date: e.target.value })}
                    className="w-[130px]"
                  />
                </div>
                <div className="flex gap-2">
                  <Button size="sm" onClick={onCreateTask}>
                    Add
                  </Button>
                  <Button size="sm" variant="outline" onClick={onCancelTaskForm}>
                    Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  resetTaskForm();
                  setCreatingTaskForDecision(decision.id);
                }}
              >
                <Plus className="h-4 w-4 mr-2" />
                Add Task
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

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
      <div className="p-3 bg-background border rounded-md">
        <div className="flex gap-2 flex-wrap">
          <Input
            value={formData.title}
            onChange={(e) => setFormData({ ...formData, title: e.target.value })}
            placeholder="Task title"
            className="flex-1"
          />
          <Select
            value={formData.status}
            onValueChange={(value) => setFormData({ ...formData, status: value as TaskStatus })}
          >
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="in_progress">In Progress</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
            </SelectContent>
          </Select>
          <Input
            type="date"
            value={formData.due_date}
            onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            className="w-[130px]"
          />
        </div>
        <div className="flex gap-2 mt-2">
          <Button size="sm" onClick={onUpdate}>
            Save
          </Button>
          <Button size="sm" variant="outline" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
      <div className="flex items-center gap-3">
        {task.status === 'completed' ? (
          <Check className="h-5 w-5 text-green-500" />
        ) : task.status === 'in_progress' ? (
          <div className="h-5 w-5 rounded-full border-2 border-blue-500" />
        ) : (
          <div className="h-5 w-5 rounded-full border-2 border-gray-400" />
        )}
        <span className={task.status === 'completed' ? 'line-through text-muted-foreground' : ''}>
          {task.title}
        </span>
        {task.due_date && (
          <span className="text-sm text-muted-foreground">due: {task.due_date}</span>
        )}
        <Badge variant="outline" className="text-xs">
          {task.status.replace('_', ' ')}
        </Badge>
      </div>
      <div className="flex gap-1">
        <Button variant="ghost" size="sm" onClick={onEdit}>
          <Pencil className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onDelete}>
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
