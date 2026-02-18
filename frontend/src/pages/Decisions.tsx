import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { decisionsApi, Decision, directionsApi } from '../utils/api';

export default function Decisions() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    date: new Date().toISOString().split('T')[0],
    status: 'ongoing' as 'completed' | 'ongoing' | 'archived',
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
            <div key={decision.id} className="list-item">
              <div className="list-item-content">
                <div className="list-item-title">{decision.title}</div>
                <div className="list-item-meta">
                  <span className={`status-badge status-${decision.status}`}>
                    {decision.status}
                  </span>
                  <span>Created: {decision.date}</span>
                  {decision.review_at && <span>Review: {decision.review_at}</span>}
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
