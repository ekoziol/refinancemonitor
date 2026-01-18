import React, { useState, createContext, useContext } from 'react';
import { cn } from '../../lib/utils';
import Sidebar from './Sidebar';

/**
 * Context for dashboard layout state management.
 * Provides sidebar collapsed state to child components.
 */
const DashboardLayoutContext = createContext({
  isSidebarCollapsed: false,
  setIsSidebarCollapsed: () => {},
});

/**
 * Hook to access dashboard layout context.
 */
export function useDashboardLayout() {
  return useContext(DashboardLayoutContext);
}

/**
 * DashboardHeader - Top header bar for the dashboard.
 * Displays page title and optional actions.
 */
function DashboardHeader({
  title,
  subtitle,
  children,
  className,
}) {
  return (
    <header className={cn('dashboard-header', className)}>
      <div className="flex-1 min-w-0">
        {title && (
          <h1 className="text-xl font-semibold text-foreground truncate">
            {title}
          </h1>
        )}
        {subtitle && (
          <p className="text-sm text-muted-foreground truncate">
            {subtitle}
          </p>
        )}
      </div>
      {children && (
        <div className="flex items-center gap-4">
          {children}
        </div>
      )}
    </header>
  );
}

/**
 * DashboardMain - Main content area container.
 * Provides proper padding and scrolling for dashboard content.
 */
function DashboardMain({ children, className }) {
  return (
    <main className={cn('dashboard-main', className)}>
      {children}
    </main>
  );
}

/**
 * DashboardGrid - Grid layout for dashboard cards.
 * Responsive grid that adapts to screen size.
 */
function DashboardGrid({
  children,
  columns = 3,
  className,
}) {
  const gridCols = {
    1: 'grid-cols-1',
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div
      className={cn(
        'grid gap-6',
        gridCols[columns] || gridCols[3],
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * DashboardSection - Section wrapper with optional title.
 */
function DashboardSection({
  title,
  description,
  children,
  className,
}) {
  return (
    <section className={cn('space-y-4', className)}>
      {(title || description) && (
        <div className="space-y-1">
          {title && (
            <h2 className="text-lg font-semibold text-foreground">
              {title}
            </h2>
          )}
          {description && (
            <p className="text-sm text-muted-foreground">
              {description}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}

/**
 * DashboardLayout - Main layout component with glass-morphism sidebar.
 *
 * Provides a responsive dashboard layout with:
 * - Collapsible sidebar navigation
 * - Main content area with proper margins
 * - Header with title and actions
 * - Context for layout state
 *
 * @param {Object} props
 * @param {React.ReactNode} props.children - Main content
 * @param {string} props.userName - Current user's name for sidebar
 * @param {string} props.activeNavItem - Currently active navigation item
 * @param {Array} props.navItems - Custom navigation items
 * @param {boolean} props.defaultCollapsed - Start with sidebar collapsed
 * @param {Function} props.onNavigate - Navigation callback
 * @param {string} props.className - Additional CSS classes
 */
function DashboardLayout({
  children,
  userName,
  activeNavItem = 'home',
  navItems,
  defaultCollapsed = false,
  onNavigate,
  className,
}) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(defaultCollapsed);

  return (
    <DashboardLayoutContext.Provider
      value={{ isSidebarCollapsed, setIsSidebarCollapsed }}
    >
      <div className={cn('dashboard-layout dark', className)}>
        <Sidebar
          userName={userName}
          activeItemId={activeNavItem}
          navItems={navItems}
          defaultCollapsed={defaultCollapsed}
          onNavigate={onNavigate}
        />
        <div
          className={cn(
            'main-content flex flex-col',
            isSidebarCollapsed && 'main-content-collapsed'
          )}
        >
          {children}
        </div>
      </div>
    </DashboardLayoutContext.Provider>
  );
}

// Export all components
export {
  DashboardLayout,
  DashboardHeader,
  DashboardMain,
  DashboardGrid,
  DashboardSection,
};

export default DashboardLayout;
