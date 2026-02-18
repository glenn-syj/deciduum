import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { directionsApi, Direction, Decision, Memo } from '../utils/api';

interface DirectionDetails {
  direction: Direction;
  decisions: Decision[];
  memos: Memo[];
}

export default function Directions() {
  const queryClient = useQueryClient();
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [selectedDirectionId, setSelectedDirectionId] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
  });

  const { data: directionsData, isLoading } = useQuery({
    queryKey: ['directions'],
    queryFn: async () => {
      const response = await directionsApi.list();
      return response.data;
    },
  });

  const { data: directionDetails } = useQuery({
    queryKey: ['direction-details', selectedDirectionId],
    queryFn: async () => {
      if (!selectedDirectionId) return null;
      const response = await directionsApi.getDetails(selectedDirectionId);
      return response.data as DirectionDetails;
    },
    enabled: !!selectedDirectionId,
  });

  const createMutation = useMutation({
    mutationFn: (data: Partial<Direction>) => directionsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directions'] });
      setIsCreating(false);
      resetForm();
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Direction> }) =>
      directionsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directions'] });
      setEditingId(null);
      resetForm();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => directionsApi.delete(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ['directions'] });
      if (selectedDirectionId === deletedId) {
        setSelectedDirectionId(null);
      }
    },
  });

  const resetForm = () => {
    setFormData({
      title: '',
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData: Partial<Direction> = {
      title: formData.title,
    };

    if (editingId) {
      updateMutation.mutate({ id: editingId, data: submitData });
    } else {
      createMutation.mutate(submitData);
    }
  };

  const handleEdit = (direction: Direction) => {
    setEditingId(direction.id);
    setFormData({
      title: direction.title,
    });
    setIsCreating(true);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this direction?')) {
      deleteMutation.mutate(id);
    }
  };

  const cancelForm = () => {
    setIsCreating(false);
    setEditingId(null);
    resetForm();
  };

  const closeDetails = () => {
    setSelectedDirectionId(null);
  };

  if (isLoading) {
    return (
      <div className="page">
        <div className="page-header">
          <h1>Directions</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  const directions = directionsData?.data || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Directions</h1>
        {!isCreating && (
          <button className="btn btn-primary" onClick={() => setIsCreating(true)}>
            + New Direction
          </button>
        )}
      </div>

      {isCreating && (
        <div className="card form-card">
          <h2 className="card-title">
            {editingId ? 'Edit Direction' : 'New Direction'}
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

      <div className="directions-layout">
        <div className="directions-list-section">
          {directions.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">🧭</div>
              <p>No directions yet. Create your first direction!</p>
            </div>
          ) : (
            <div className="list">
              {directions.map((direction) => (
                <div
                  key={direction.id}
                  className={`list-item direction-item ${
                    selectedDirectionId === direction.id ? 'selected' : ''
                  }`}
                >
                  <div
                    className="list-item-content"
                    onClick={() => setSelectedDirectionId(direction.id)}
                  >
                    <div className="list-item-title">{direction.title}</div>
                    <div className="list-item-meta">
                      Created: {direction.created_at?.split('T')[0]}
                    </div>
                  </div>
                  <div className="list-item-actions">
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleEdit(direction)}
                    >
                      Edit
                    </button>
                    <button
                      className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(direction.id)}
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedDirectionId && directionDetails && (
          <div className="direction-details-section">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">{directionDetails.direction.title}</h2>
                <button className="btn btn-secondary btn-sm" onClick={closeDetails}>
                  Close
                </button>
              </div>

              <div className="direction-details-content">
                <section className="details-section">
                  <h3>Decisions ({directionDetails.decisions.length})</h3>
                  {directionDetails.decisions.length === 0 ? (
                    <p className="empty-text">No decisions in this direction</p>
                  ) : (
                    <ul className="details-list">
                      {directionDetails.decisions.map((decision) => (
                        <li key={decision.id} className="details-list-item">
                          <span className="details-list-title">{decision.title}</span>
                          <span className={`status-badge status-${decision.status}`}>
                            {decision.status}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>

                <section className="details-section">
                  <h3>Memos ({directionDetails.memos.length})</h3>
                  {directionDetails.memos.length === 0 ? (
                    <p className="empty-text">No memos in this direction</p>
                  ) : (
                    <ul className="details-list">
                      {directionDetails.memos.map((memo) => (
                        <li key={memo.id} className="details-list-item">
                          <span className="details-list-content">{memo.content}</span>
                          <span className="details-list-meta">{memo.date}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </section>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
