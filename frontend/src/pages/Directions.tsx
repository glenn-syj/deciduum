import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { directionsApi, Direction, Decision, Memo } from '../utils/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Plus, Pencil, Trash2, X, Compass } from 'lucide-react';

interface DirectionDetails {
  direction: Direction;
  decisions: Decision[];
  memos: Memo[];
}

function getStatusVariant(status: string) {
  switch (status) {
    case 'completed':
      return 'default';
    case 'ongoing':
      return 'outline';
    case 'archived':
      return 'secondary';
    default:
      return 'outline';
  }
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
      <div className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Directions</h1>
          <p className="text-sm text-muted-foreground">Loading directions...</p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-32 bg-muted/50 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const directions = directionsData?.data || [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Directions</h1>
          <p className="text-sm text-muted-foreground mt-1">Define the directions that guide your decisions</p>
        </div>
        {!isCreating && (
          <Button onClick={() => setIsCreating(true)} className="shadow-sm hover:shadow-md transition-shadow">
            <Plus className="mr-2 h-4 w-4" />
            New Direction
          </Button>
        )}
      </div>

      {isCreating && (
        <Card className="shadow-sm border-border/50">
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Direction' : 'New Direction'}</CardTitle>
          </CardHeader>
          <CardContent className="p-6">
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          {directions.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="rounded-full bg-muted p-4 mb-4">
                <Compass className="h-8 w-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold">No directions yet</h3>
              <p className="text-sm text-muted-foreground mt-1">Create your first direction to get started</p>
            </div>
          ) : (
            <div className="space-y-3">
              {directions.map((direction) => (
                <Card 
                  key={direction.id} 
                  className={`cursor-pointer transition-all duration-200 shadow-sm hover:shadow-md border-border/50 ${selectedDirectionId === direction.id ? 'border-primary ring-1 ring-primary' : ''}`}
                  onClick={() => setSelectedDirectionId(direction.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium">{direction.title}</h3>
                        <p className="text-sm text-muted-foreground mt-1">
                          Created: {direction.created_at?.split('T')[0]}
                        </p>
                      </div>
                      <div className="flex gap-1" onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="sm" onClick={() => handleEdit(direction)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(direction.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>

        {selectedDirectionId && directionDetails && (
          <div>
            <Card className="shadow-sm border-border/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>{directionDetails.direction.title}</CardTitle>
                  <Button variant="ghost" size="sm" onClick={closeDetails}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-6">
                  <div>
                    <h3 className="font-semibold mb-3">Decisions ({directionDetails.decisions.length})</h3>
                    {directionDetails.decisions.length === 0 ? (
                      <p className="text-muted-foreground text-sm">No decisions in this direction</p>
                    ) : (
                      <ul className="space-y-2">
                        {directionDetails.decisions.map((decision) => (
                          <li key={decision.id} className="flex items-center justify-between p-2 bg-muted/50 rounded-md">
                            <span className="text-sm">{decision.title}</span>
                            <Badge variant={getStatusVariant(decision.status) as any}>
                              {decision.status}
                            </Badge>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <Separator />

                  <div>
                    <h3 className="font-semibold mb-3">Memos ({directionDetails.memos.length})</h3>
                    {directionDetails.memos.length === 0 ? (
                      <p className="text-muted-foreground text-sm">No memos in this direction</p>
                    ) : (
                      <ul className="space-y-2">
                        {directionDetails.memos.map((memo) => (
                          <li key={memo.id} className="p-2 bg-muted/50 rounded-md">
                            <p className="text-sm truncate">{memo.content}</p>
                            <p className="text-xs text-muted-foreground">{memo.date}</p>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
