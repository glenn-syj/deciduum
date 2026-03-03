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
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['directions'] });
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
    if (confirm('Delete this direction? This cannot be undone.')) {
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
          <h1>Directions</h1>
        </div>
        <div className="loading">Loading...</div>
      </div>
    );
  }

  const directions = directionsData?.directions || [];

  return (
    <div className="page">
      <div className="page-header">
        <h1>Directions</h1>
      </div>

      {isCreating && (
        <div className="form-section">
          <h3>{editingId ? '> Edit Direction' : '> New Direction'}</h3>
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

            <div className="form-actions">
              <button type="submit">{editingId ? '[save]' : '[create]'}</button>
              <button type="button" onClick={cancelForm}>[cancel]</button>
            </div>
          </form>
        </div>
      )}

      {!isCreating && (
        <button className="btn-link" onClick={() => setIsCreating(true)}>+ create new direction</button>
      )}

      {directions.length === 0 ? (
        <div className="empty-state">
          <p>No directions yet.</p>
        </div>
      ) : (
        <div className="directions-list">
          {directions.map((direction) => (
            <DirectionItem
              key={direction.id}
              direction={direction}
              isExpanded={expandedIds.has(direction.id)}
              onToggle={() => toggleExpanded(direction.id)}
              onEdit={() => handleEdit(direction)}
              onDelete={() => handleDelete(direction.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface DirectionItemProps {
  direction: Direction;
  isExpanded: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

function DirectionItem({
  direction,
  isExpanded,
  onToggle,
  onEdit,
  onDelete,
}: DirectionItemProps) {
  const { data: detailsData } = useQuery({
    queryKey: ['direction-details', direction.id],
    queryFn: async () => {
      const response = await directionsApi.getDetails(direction.id);
      return response.data as DirectionDetails;
    },
    enabled: !!direction.id,
  });

  const details = detailsData;

  return (
    <div className="direction-item">
      {/* Main direction line */}
      <div className="direction-main">
        <span>* {direction.title}</span>
        <span> </span>
        <button className="btn-link" onClick={onToggle}>
          {isExpanded ? '[-]' : '[+]'}
        </button>
      </div>

      {/* Expanded content with decisions and memos */}
      {isExpanded && details && (
        <div className="direction-expanded">
          {/* Decision count */}
          <div className="direction-meta">
            <span>  - Decisions: {details.decisions.length}</span>
          </div>

          {/* Decisions list */}
          {details.decisions.length > 0 && (
            <div className="direction-decisions">
              {details.decisions.map(decision => (
                <div key={decision.id} className="direction-decision-item">
                  <span>  - [{decision.status}] {decision.title}</span>
                </div>
              ))}
            </div>
          )}

          {/* Memos count */}
          <div className="direction-meta">
            <span>  - Memos: {details.memos.length}</span>
          </div>

          {/* Memos list */}
          {details.memos.length > 0 && (
            <div className="direction-memos">
              {details.memos.map(memo => (
                <div key={memo.id} className="direction-memo-item">
                  <span>  - {memo.date}: {memo.content.substring(0, 50)}{memo.content.length > 50 ? '...' : ''}</span>
                </div>
              ))}
            </div>
          )}

          {/* Action links */}
          <div className="direction-actions">
            <button className="btn-link" onClick={onEdit}>[edit]</button>
            <button className="btn-link" onClick={onDelete}>[delete]</button>
          </div>
        </div>
      )}
    </div>
  );
}
