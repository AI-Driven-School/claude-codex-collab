'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/ui/header';
import { IconBuilding, IconPlus, IconTrash, IconPencil, IconLoader } from '@/components/ui/icons';
import { departmentApi, Department } from '@/lib/api/department';

export default function DepartmentAdminPage() {
  const router = useRouter();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [newDept, setNewDept] = useState({ name: '', description: '' });
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingValues, setEditingValues] = useState({ name: '', description: '' });

  const loadDepartments = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await departmentApi.getDepartments();
      setDepartments(response.departments);
    } catch (err: any) {
      setError(err.response?.data?.detail || '部署の取得に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDepartments();
  }, []);

  const handleCreate = async () => {
    if (!newDept.name.trim()) {
      setError('部署名を入力してください');
      return;
    }
    setSaving(true);
    try {
      await departmentApi.createDepartment({
        name: newDept.name.trim(),
        description: newDept.description.trim() || undefined,
      });
      setNewDept({ name: '', description: '' });
      await loadDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || '部署の作成に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (dept: Department) => {
    setEditingId(dept.id);
    setEditingValues({
      name: dept.name,
      description: dept.description || '',
    });
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingValues({ name: '', description: '' });
  };

  const handleUpdate = async () => {
    if (!editingId) return;
    if (!editingValues.name.trim()) {
      setError('部署名を入力してください');
      return;
    }
    setSaving(true);
    try {
      await departmentApi.updateDepartment(editingId, {
        name: editingValues.name.trim(),
        description: editingValues.description.trim() || undefined,
      });
      await loadDepartments();
      cancelEdit();
    } catch (err: any) {
      setError(err.response?.data?.detail || '部署の更新に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (dept: Department) => {
    if (!confirm(`部署「${dept.name}」を削除しますか？`)) return;
    setSaving(true);
    try {
      await departmentApi.deleteDepartment(dept.id);
      await loadDepartments();
    } catch (err: any) {
      setError(err.response?.data?.detail || '部署の削除に失敗しました');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="page-container">
      <Header title="部署管理" />

      <main className="page-content">
        <div className="card p-6 mb-6 animate-fade-in">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary-100 to-primary-200 flex items-center justify-center">
              <IconBuilding className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-sand-900">部署管理</h1>
              <p className="text-sm text-sand-600">部署の追加・編集・削除</p>
            </div>
          </div>
        </div>

        {error && (
          <div className="alert-danger mb-6 animate-fade-in-down">{error}</div>
        )}

        <div className="card p-6 mb-6 animate-fade-in">
          <h2 className="font-bold text-sand-900 mb-4">新規部署の追加</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              className="input"
              placeholder="部署名"
              value={newDept.name}
              onChange={(e) => setNewDept({ ...newDept, name: e.target.value })}
            />
            <input
              className="input"
              placeholder="説明（任意）"
              value={newDept.description}
              onChange={(e) => setNewDept({ ...newDept, description: e.target.value })}
            />
            <button
              onClick={handleCreate}
              disabled={saving}
              className="btn-primary"
            >
              <IconPlus className="w-4 h-4" />
              追加
            </button>
          </div>
        </div>

        <div className="card p-6 animate-fade-in">
          <h2 className="font-bold text-sand-900 mb-4">部署一覧</h2>
          {loading ? (
            <div className="text-center py-8">
              <IconLoader className="w-6 h-6 animate-spin text-primary-500 mx-auto mb-2" />
              <p className="text-sand-600">読み込み中...</p>
            </div>
          ) : departments.length === 0 ? (
            <div className="text-center py-8 text-sand-500">部署がありません</div>
          ) : (
            <div className="space-y-3">
              {departments.map((dept) => (
                <div key={dept.id} className="p-4 bg-sand-50 rounded-xl border border-sand-200">
                  {editingId === dept.id ? (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <input
                        className="input"
                        value={editingValues.name}
                        onChange={(e) => setEditingValues({ ...editingValues, name: e.target.value })}
                      />
                      <input
                        className="input"
                        value={editingValues.description}
                        onChange={(e) => setEditingValues({ ...editingValues, description: e.target.value })}
                      />
                      <div className="flex gap-2">
                        <button className="btn-primary flex-1" onClick={handleUpdate} disabled={saving}>
                          更新
                        </button>
                        <button className="btn-secondary flex-1" onClick={cancelEdit} disabled={saving}>
                          キャンセル
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between gap-4">
                      <div>
                        <div className="font-medium text-sand-800">{dept.name}</div>
                        <div className="text-sm text-sand-500">
                          {dept.description || '説明なし'} ・ 従業員数 {dept.employee_count} 名
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button className="btn-secondary" onClick={() => startEdit(dept)}>
                          <IconPencil className="w-4 h-4" />
                          編集
                        </button>
                        <button className="btn-ghost text-danger" onClick={() => handleDelete(dept)}>
                          <IconTrash className="w-4 h-4" />
                          削除
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6">
          <button className="btn-ghost" onClick={() => router.push('/dashboard')}>
            ダッシュボードに戻る
          </button>
        </div>
      </main>
    </div>
  );
}
