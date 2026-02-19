import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as Select from '@radix-ui/react-select';
import * as Dialog from '@radix-ui/react-dialog';
import { memosApi, Memo, decisionsApi, directionsApi } from '../utils/api';

function SelectField({ 
  label, 
  value, 
  onValueChange, 
  placeholder,
  options,
}: { 
  label: string;
  value: string;
  onValueChange: (value: string) => void;
  placeholder?: string;
  options: { id: string; title: string }[];
}) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <Select.Root value={value || 'none'} onValueChange={(v) => onValueChange(v === 'none' ? '' : v)}>
        <Select.Trigger className="select-trigger">
          <Select.Value placeholder={placeholder || 'Select...'} />
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
                <Select.ItemText>{placeholder || 'None'}</Select.ItemText>
              </Select.Item>
              {options.map((option) => (
                <Select.Item key={option.id} value={option.id} className="select-item">
                  <Select.ItemText>{option.title}</Select.ItemText>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select.Portal>
      </Select.Root>
    </div>
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
          <Dialog.Title className="dialog-title">Delete Memo</Dialog.Title>
          <Dialog.Description className="dialog-description">
            Are you sure you want to delete this memo? This action cannot be undone.
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

export default function Memos() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
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

              <SelectField
                label="Linked Decision"
                value={formData.linked_decision_id}
                onValueChange={(value) => setFormData({ ...formData, linked_decision_id: value })}
                placeholder="None"
                options={decisions.map(d => ({ id: d.id, title: d.title }))}
              />

              <SelectField
                label="Linked Direction"
                value={formData.linked_direction_id}
                onValueChange={(value) => setFormData({ ...formData, linked_direction_id: value })}
                placeholder="None"
                options={directions.map(d => ({ id: d.id, title: d.title }))}
              />
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
                  onClick={() => handleDeleteClick(memo.id)}
                >
                  Delete
                </button>
              </div>
            </div>
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
