/**
 * AlertCard component with inline threshold editing.
 *
 * Displays alert information with the ability to edit threshold values inline.
 * Uses PATCH /api/alerts/{id} for partial updates.
 */
import * as React from 'react';
import { useState, useCallback } from 'react';
import { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { usePatchAlertThreshold } from '../api/hooks';

const STATUS_STYLES = {
  active: 'bg-green-100 text-green-800 border-green-200',
  paused: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  triggered: 'bg-blue-100 text-blue-800 border-blue-200',
  waiting: 'bg-gray-100 text-gray-600 border-gray-200',
};

const STATUS_LABELS = {
  active: 'Active',
  paused: 'Paused',
  triggered: 'Triggered',
  waiting: 'Waiting',
};

function ThresholdField({ label, value, isEditing, editValue, onChange, type = 'number', prefix = '', suffix = '' }) {
  if (isEditing) {
    return (
      <div className="flex flex-col gap-1">
        <label className="text-xs text-gray-500">{label}</label>
        <div className="flex items-center gap-1">
          {prefix && <span className="text-sm text-gray-500">{prefix}</span>}
          <Input
            type={type}
            value={editValue}
            onChange={(e) => onChange(e.target.value)}
            className="h-8 w-24"
            step={type === 'number' ? '0.01' : undefined}
          />
          {suffix && <span className="text-sm text-gray-500">{suffix}</span>}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-sm font-medium">
        {prefix}{value !== null && value !== undefined ? value : '--'}{suffix}
      </span>
    </div>
  );
}

export default function AlertCard({ alert, mortgageName, onPause, onResume, onDelete }) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState({
    target_interest_rate: alert.target_interest_rate ?? '',
    target_monthly_payment: alert.target_monthly_payment ?? '',
    target_term: alert.target_term ?? '',
    estimate_refinance_cost: alert.estimate_refinance_cost ?? '',
  });

  const patchMutation = usePatchAlertThreshold();

  const handleEditToggle = useCallback(() => {
    if (isEditing) {
      // Cancel - reset to original values
      setEditValues({
        target_interest_rate: alert.target_interest_rate ?? '',
        target_monthly_payment: alert.target_monthly_payment ?? '',
        target_term: alert.target_term ?? '',
        estimate_refinance_cost: alert.estimate_refinance_cost ?? '',
      });
    }
    setIsEditing(!isEditing);
  }, [isEditing, alert]);

  const handleSave = useCallback(async () => {
    const data = {};

    // Only include changed values
    if (editValues.target_interest_rate !== '' && editValues.target_interest_rate !== alert.target_interest_rate) {
      data.target_interest_rate = parseFloat(editValues.target_interest_rate);
    }
    if (editValues.target_monthly_payment !== '' && editValues.target_monthly_payment !== alert.target_monthly_payment) {
      data.target_monthly_payment = parseFloat(editValues.target_monthly_payment);
    }
    if (editValues.target_term !== '' && editValues.target_term !== alert.target_term) {
      data.target_term = parseInt(editValues.target_term, 10);
    }
    if (editValues.estimate_refinance_cost !== '' && editValues.estimate_refinance_cost !== alert.estimate_refinance_cost) {
      data.estimate_refinance_cost = parseFloat(editValues.estimate_refinance_cost);
    }

    if (Object.keys(data).length === 0) {
      setIsEditing(false);
      return;
    }

    try {
      await patchMutation.mutateAsync({ id: alert.id, data });
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to update alert threshold:', error);
    }
  }, [alert, editValues, patchMutation]);

  const handleFieldChange = useCallback((field, value) => {
    setEditValues((prev) => ({ ...prev, [field]: value }));
  }, []);

  const statusStyle = STATUS_STYLES[alert.status] || STATUS_STYLES.waiting;
  const statusLabel = STATUS_LABELS[alert.status] || 'Unknown';

  const formatRate = (rate) => {
    if (rate === null || rate === undefined) return '--';
    return `${(rate * 100).toFixed(2)}%`;
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '--';
    return `$${parseFloat(amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatTerm = (months) => {
    if (months === null || months === undefined) return '--';
    const years = Math.floor(months / 12);
    const remainingMonths = months % 12;
    if (remainingMonths === 0) return `${years} years`;
    return `${years}y ${remainingMonths}mo`;
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{mortgageName || `Alert #${alert.id}`}</CardTitle>
            <CardDescription className="mt-1">
              {alert.alert_type === 'rate' ? 'Interest Rate Alert' : 'Payment Alert'}
            </CardDescription>
          </div>
          <Badge className={statusStyle}>{statusLabel}</Badge>
        </div>
      </CardHeader>

      <CardContent>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {alert.alert_type === 'rate' ? (
            <ThresholdField
              label="Target Rate"
              value={formatRate(alert.target_interest_rate)}
              isEditing={isEditing}
              editValue={editValues.target_interest_rate}
              onChange={(v) => handleFieldChange('target_interest_rate', v)}
              suffix="%"
            />
          ) : (
            <ThresholdField
              label="Target Payment"
              value={formatCurrency(alert.target_monthly_payment)}
              isEditing={isEditing}
              editValue={editValues.target_monthly_payment}
              onChange={(v) => handleFieldChange('target_monthly_payment', v)}
              prefix="$"
            />
          )}

          <ThresholdField
            label="Term"
            value={formatTerm(alert.target_term)}
            isEditing={isEditing}
            editValue={editValues.target_term}
            onChange={(v) => handleFieldChange('target_term', v)}
            suffix=" months"
          />

          <ThresholdField
            label="Refi Cost Est."
            value={formatCurrency(alert.estimate_refinance_cost)}
            isEditing={isEditing}
            editValue={editValues.estimate_refinance_cost}
            onChange={(v) => handleFieldChange('estimate_refinance_cost', v)}
            prefix="$"
          />

          <div className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Created</span>
            <span className="text-sm font-medium">
              {alert.created_on ? new Date(alert.created_on).toLocaleDateString() : '--'}
            </span>
          </div>
        </div>
      </CardContent>

      <CardFooter className="flex justify-between gap-2 pt-3 border-t border-gray-100">
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button
                variant="default"
                size="sm"
                onClick={handleSave}
                disabled={patchMutation.isPending}
              >
                {patchMutation.isPending ? 'Saving...' : 'Save'}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEditToggle}
                disabled={patchMutation.isPending}
              >
                Cancel
              </Button>
            </>
          ) : (
            <Button variant="outline" size="sm" onClick={handleEditToggle}>
              Edit Thresholds
            </Button>
          )}
        </div>

        <div className="flex gap-2">
          {alert.status === 'paused' ? (
            <Button variant="secondary" size="sm" onClick={() => onResume?.(alert.id)}>
              Resume
            </Button>
          ) : alert.status === 'active' ? (
            <Button variant="secondary" size="sm" onClick={() => onPause?.(alert.id)}>
              Pause
            </Button>
          ) : null}
          <Button variant="destructive" size="sm" onClick={() => onDelete?.(alert.id)}>
            Delete
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}
