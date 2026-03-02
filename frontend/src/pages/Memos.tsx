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
    if (confirm('Delete this memo? This cannot be undone.')) {
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
      </div>

      {isCreating && (
        <div className="form-section">
          <h3>{editingId ? '> Edit Memo' : '> New Memo'}</h3>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label>Content: </label>
              <textarea
                rows={4}
                value={formData.content}
                onChange={(e) => setFormData({ ...formData, content: e.target.value })}
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
                <label>Decision: </label>
                <select
                  value={formData.linked_decision_id}
                  onChange={(e) => setFormData({ ...formData, linked_decision_id: e.target.value })}
                >
                  <option value="">None</option>
                  {decisions.map(decision => (
                    <option key={decision.id} value={decision.id}>{decision.title}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Direction: </label>
                <select
                  value={formData.linked_direction_id}
                  onChange={(e) => setFormData({ ...formData, linked_direction_id: e.target.value })}
                >
                  <option value="">None</option>
                  {directions.map(direction => (
                    <option key={direction.id} value={direction.id}>{direction.title}</option>
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
        <button className="btn-link" onClick={() => setIsCreating(true)}>+ create new memo</button>
      )}

      {memos.length === 0 ? (
        <div className="empty-state">
          <p>No memos yet.</p>
        </div>
      ) : (
        <div className="memos-list">
          <h3>--- Memos ---</h3>
          {memos.map((memo) => (
            <MemoItem
              key={memo.id}
              memo={memo}
              onEdit={() => handleEdit(memo)}
              onDelete={() => handleDelete(memo.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface MemoItemProps {
  memo: Memo;
  onEdit: () => void;
  onDelete: () => void;
}

function MemoItem({ memo, onEdit, onDelete }: MemoItemProps) {
  const [expanded, setExpanded] = useState(false);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toISOString().split('T')[0];
  };

  return (
    <div className="memo-item">
      <div className="memo-main">
        <span>- {formatDate(memo.date)}: </span>
        <span>{memo.content}</span>
        <span> </span>
        <button className="btn-link" onClick={() => setExpanded(!expanded)}>
          {expanded ? '[-]' : '[+]'}
        </button>
      </div>

      {expanded && (
        <div className="memo-expanded">
          <div className="memo-actions">
            <button className="btn-link" onClick={onEdit}>[edit]</button>
            <button className="btn-link" onClick={onDelete}>[delete]</button>
          </div>
          {memo.linked_decision_id && (
            <div className="memo-link">
              <span>Linked to decision: {memo.linked_decision_id}</span>
            </div>
          )}
          {memo.linked_direction_id && (
            <div className="memo-link">
              <span>Linked to direction: {memo.linked_direction_id}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
