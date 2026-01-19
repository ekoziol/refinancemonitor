/**
 * Dashboard - Main dashboard page component.
 *
 * Integrates all dashboard components:
 * - MetricCards for KPI display
 * - MortgageCard for mortgage listing
 * - RefiTriggerPoint for decision support
 * - AlertCard for alert management
 */
import * as React from 'react';
import { useState, useCallback } from 'react';
import {
  DashboardLayout,
  DashboardHeader,
  DashboardMain,
  DashboardGrid,
  DashboardSection,
} from './layout';
import MetricCards from './MetricCards';
import MortgageCard from './MortgageCard';
import RefiTriggerPoint from './RefiTriggerPoint';
import AlertCard from './AlertCard';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import {
  useMortgages,
  useDeleteMortgage,
  useAlerts,
  usePauseAlert,
  useResumeAlert,
  useDeleteAlert,
  useKpiMetrics,
} from '../api';

/**
 * Empty state component for sections with no data.
 */
function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <Card className="w-full border-dashed">
      <CardContent className="py-12 text-center">
        <h3 className="text-lg font-medium text-foreground mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{description}</p>
        {onAction && actionLabel && (
          <Button onClick={onAction}>{actionLabel}</Button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Error state component.
 */
function ErrorState({ title, message, onRetry }) {
  return (
    <Card className="w-full border-destructive">
      <CardContent className="py-8 text-center">
        <h3 className="text-lg font-medium text-destructive mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground mb-4">{message}</p>
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            Try Again
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Add new card button component.
 */
function AddNewCard({ label, onClick }) {
  return (
    <Card
      className="w-full border-dashed cursor-pointer hover:bg-accent/50 transition-colors"
      onClick={onClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      <CardContent className="py-12 text-center">
        <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-primary/10 flex items-center justify-center">
          <svg
            className="w-6 h-6 text-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4v16m8-8H4"
            />
          </svg>
        </div>
        <span className="text-sm font-medium text-primary">{label}</span>
      </CardContent>
    </Card>
  );
}

/**
 * Dashboard page component.
 *
 * @param {Object} props
 * @param {string} [props.userName] - Current user's name for sidebar
 * @param {Function} [props.onAddMortgage] - Callback to add new mortgage
 * @param {Function} [props.onEditMortgage] - Callback to edit mortgage
 * @param {Function} [props.onAddAlert] - Callback to add new alert
 * @param {Function} [props.onNavigate] - Navigation callback for sidebar
 */
export default function Dashboard({
  userName = 'User',
  onAddMortgage,
  onEditMortgage,
  onAddAlert,
  onNavigate,
}) {
  // Selected mortgage for KPI display
  const [selectedMortgageId, setSelectedMortgageId] = useState(null);

  // Data fetching
  const {
    data: mortgages,
    isLoading: mortgagesLoading,
    error: mortgagesError,
    refetch: refetchMortgages,
  } = useMortgages();

  const {
    data: alerts,
    isLoading: alertsLoading,
    error: alertsError,
    refetch: refetchAlerts,
  } = useAlerts();

  const {
    data: kpiData,
    isLoading: kpiLoading,
  } = useKpiMetrics(selectedMortgageId);

  // Mutations
  const deleteMortgageMutation = useDeleteMortgage();
  const pauseAlertMutation = usePauseAlert();
  const resumeAlertMutation = useResumeAlert();
  const deleteAlertMutation = useDeleteAlert();

  // Get first mortgage ID if none selected
  const effectiveMortgageId =
    selectedMortgageId || (mortgages && mortgages.length > 0 ? mortgages[0].id : null);

  // Count alerts per mortgage
  const alertCountByMortgage = React.useMemo(() => {
    if (!alerts) return {};
    return alerts.reduce((acc, alert) => {
      acc[alert.mortgage_id] = (acc[alert.mortgage_id] || 0) + 1;
      return acc;
    }, {});
  }, [alerts]);

  // Get mortgage name for selected mortgage
  const selectedMortgage = React.useMemo(() => {
    if (!mortgages || !effectiveMortgageId) return null;
    return mortgages.find((m) => m.id === effectiveMortgageId);
  }, [mortgages, effectiveMortgageId]);

  // Handlers
  const handleSelectMortgage = useCallback((id) => {
    setSelectedMortgageId(id);
  }, []);

  const handleDeleteMortgage = useCallback(
    async (id) => {
      if (window.confirm('Are you sure you want to delete this mortgage? This action cannot be undone.')) {
        try {
          await deleteMortgageMutation.mutateAsync(id);
          if (selectedMortgageId === id) {
            setSelectedMortgageId(null);
          }
        } catch (error) {
          console.error('Failed to delete mortgage:', error);
        }
      }
    },
    [deleteMortgageMutation, selectedMortgageId]
  );

  const handlePauseAlert = useCallback(
    async (id) => {
      try {
        await pauseAlertMutation.mutateAsync(id);
      } catch (error) {
        console.error('Failed to pause alert:', error);
      }
    },
    [pauseAlertMutation]
  );

  const handleResumeAlert = useCallback(
    async (id) => {
      try {
        await resumeAlertMutation.mutateAsync(id);
      } catch (error) {
        console.error('Failed to resume alert:', error);
      }
    },
    [resumeAlertMutation]
  );

  const handleDeleteAlert = useCallback(
    async (id) => {
      if (window.confirm('Are you sure you want to delete this alert?')) {
        try {
          await deleteAlertMutation.mutateAsync(id);
        } catch (error) {
          console.error('Failed to delete alert:', error);
        }
      }
    },
    [deleteAlertMutation]
  );

  const handleSetAlert = useCallback(() => {
    if (onAddAlert && effectiveMortgageId) {
      onAddAlert(effectiveMortgageId);
    }
  }, [onAddAlert, effectiveMortgageId]);

  return (
    <DashboardLayout
      userName={userName}
      activeNavItem="home"
      onNavigate={onNavigate}
    >
      <DashboardHeader
        title="Dashboard"
        subtitle="Monitor your mortgages and refinance opportunities"
      >
        {onAddMortgage && (
          <Button onClick={onAddMortgage}>Add Mortgage</Button>
        )}
      </DashboardHeader>

      <DashboardMain>
        <div className="space-y-8">
          {/* KPI Metrics Section */}
          <DashboardSection title="Key Metrics">
            <MetricCards mortgageId={effectiveMortgageId} />
          </DashboardSection>

          {/* Mortgages Section */}
          <DashboardSection
            title="Your Mortgages"
            description="Select a mortgage to view its metrics and alerts"
          >
            {mortgagesError ? (
              <ErrorState
                title="Failed to load mortgages"
                message={mortgagesError.message}
                onRetry={refetchMortgages}
              />
            ) : mortgagesLoading ? (
              <DashboardGrid columns={3}>
                {[1, 2, 3].map((i) => (
                  <MortgageCard key={i} isLoading />
                ))}
              </DashboardGrid>
            ) : mortgages && mortgages.length > 0 ? (
              <DashboardGrid columns={3}>
                {mortgages.map((mortgage) => (
                  <MortgageCard
                    key={mortgage.id}
                    mortgage={mortgage}
                    alertCount={alertCountByMortgage[mortgage.id] || 0}
                    isSelected={mortgage.id === effectiveMortgageId}
                    onSelect={handleSelectMortgage}
                    onEdit={onEditMortgage}
                    onDelete={handleDeleteMortgage}
                  />
                ))}
                {onAddMortgage && (
                  <AddNewCard label="Add New Mortgage" onClick={onAddMortgage} />
                )}
              </DashboardGrid>
            ) : (
              <EmptyState
                title="No Mortgages Yet"
                description="Add your first mortgage to start tracking refinance opportunities"
                actionLabel="Add Mortgage"
                onAction={onAddMortgage}
              />
            )}
          </DashboardSection>

          {/* Refinance Decision Support Section */}
          <DashboardSection
            title="Refinance Analysis"
            description={
              selectedMortgage
                ? `Analyzing ${selectedMortgage.name}`
                : 'Select a mortgage to see analysis'
            }
          >
            <RefiTriggerPoint
              currentRate={kpiData?.your_rate}
              marketRate={kpiData?.market_rate}
              monthlySavings={kpiData?.monthly_savings}
              refiScore={kpiData?.refi_score}
              refiScoreLabel={kpiData?.refi_score_label}
              mortgageName={kpiData?.mortgage_name}
              onSetAlert={onAddAlert ? handleSetAlert : undefined}
              isLoading={kpiLoading}
            />
          </DashboardSection>

          {/* Alerts Section */}
          <DashboardSection
            title="Active Alerts"
            description="Your refinance monitoring alerts"
          >
            {alertsError ? (
              <ErrorState
                title="Failed to load alerts"
                message={alertsError.message}
                onRetry={refetchAlerts}
              />
            ) : alertsLoading ? (
              <DashboardGrid columns={2}>
                {[1, 2].map((i) => (
                  <Card key={i} className="w-full animate-pulse">
                    <CardContent className="py-8">
                      <div className="h-4 bg-muted rounded w-3/4 mb-4" />
                      <div className="h-4 bg-muted rounded w-1/2" />
                    </CardContent>
                  </Card>
                ))}
              </DashboardGrid>
            ) : alerts && alerts.length > 0 ? (
              <DashboardGrid columns={2}>
                {alerts.map((alert) => {
                  const mortgage = mortgages?.find((m) => m.id === alert.mortgage_id);
                  return (
                    <AlertCard
                      key={alert.id}
                      alert={alert}
                      mortgageName={mortgage?.name}
                      onPause={handlePauseAlert}
                      onResume={handleResumeAlert}
                      onDelete={handleDeleteAlert}
                    />
                  );
                })}
              </DashboardGrid>
            ) : (
              <EmptyState
                title="No Alerts Set"
                description="Set up alerts to be notified when refinancing conditions are favorable"
                actionLabel={effectiveMortgageId ? 'Set Alert' : undefined}
                onAction={effectiveMortgageId ? handleSetAlert : undefined}
              />
            )}
          </DashboardSection>
        </div>
      </DashboardMain>
    </DashboardLayout>
  );
}
