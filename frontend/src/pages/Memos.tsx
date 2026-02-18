import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { memosApi, Memo, decisionsApi, directionsApi } from '../utils/api';

export default function Memos() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    content: '',
    date: new Date().toISOString().split('T')[0],
    linked_decision_id: '',
    linked_direction_id: '',
  });

  const { data: memosData, isLoading } = useQuery({
    queryKey: ['memos'],
    queryFn: async () => {
      const response = await memosApi.list();
      return response.data;
    },
  });

  const { data: decisionsData } = useQuery({
    queryKey: ['decisions'],
    queryFn: async () => {
      const response = await decisionsApi.list({ limit: 100 });
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
    mutationFn: (data: Partial<Memo>) => memosApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
      setIsCreating(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Memo> }) =>
      memosApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
      setEditingId(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => memosApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memos'] });
    },
  });

  const resetForm = () => {
    setFormData({
      content: '',
      date: new Date().toISOString().split('T')[0],
      linked_decision_id: '',
      linked_direction_id: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData: Partial<Memo> = {
      content: formData.content,
      date: formData.date,
      linked_decision_id: formData.linked_decision_id || null,
      linked_direction_id: formData.linked_direction_id || null,
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleEdit = (memo: Memo) => {
    setEditingId(memo.id);
    setFormData({
      content: memo.content,
      date: memo.date,
      linked_decision_id: memo.linked_decision_id || '',
      linked_direction_id: memo.linked_direction_id || '',
    });
    setIsCreating(true);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this memo?')) {
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
          <h1>Memos</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  const memos = memosData?.data || [];
  const decisions = decisionsData?.data || [];
  const directions = directionsData?.data || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Memos</h1>
        {!isCreating && (
          <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
            + New Memo
          </button>
        )}
      </div>

      {isCreating && (
        <div className="card form-card">
          <h2 className="card-title">
            {editingId ? 'Edit Memo' : 'New Memo'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Content</label>
              <textarea
                className="form-textarea"
                rows={4}
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
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
                <label className="form-label">Linked Decision</label>
                <select
                  className="form-input"
                  value={formData.linked_decision_id}
                  onChange={(e) =>
                    setFormData({ ...formData, linked_decision_id: e.target.value })
                  }
                >
                  <option value="">None</option>
                  {decisions.map((dec) => (
                    <option key={dec.id} value={dec.id}>
                      {dec.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Linked Direction</label>
                <select
                  className="form-input"
                  value={formData.linked_direction_id}
                  onChange={(e) =>
                    setFormData({ ...formData, linked_direction_id: e.target.value })
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

      {memos.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📝</div>
          <p>No memos yet. Create your first memo!</p>
        </div>
      ) : (
        <div className="list">
          {memos.map((memo) => (
            <div key={memo.id} className="list-item">
              <div className="list-item-content">
                <div className="list-item-title memo-content">{memo.content}</div>
                <div className="list-item-meta">
                  <span>{memo.date}</span>
                  {memo.linked_decision_id && <span>Linked to decision</span>}
                  {memo.linked_direction_id && <span>Linked to direction</span>}
                </div>
              </div>
              <div className="list-item-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleEdit(memo)}
                >
                  Edit
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(memo.id)}
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
