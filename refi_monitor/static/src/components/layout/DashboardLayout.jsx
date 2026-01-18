import React, { useState, createContext, useContext } from 'react';
import { cn } from '../../lib/utils';
import Sidebar, { Icons } from './Sidebar';

/**
 * Context for dashboard layout state management.
 * Provides sidebar collapsed state and mobile menu state to child components.
 */
const DashboardLayoutContext = createContext({
  isSidebarCollapsed: false,
  setIsSidebarCollapsed: () => {},
  isMobileMenuOpen: false,
  setIsMobileMenuOpen: () => {},
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
 * MobileSidebar - Slide-out sidebar for mobile devices.
 * Renders as an overlay with the sidebar content.
 */
function MobileSidebar({
  isOpen,
  onClose,
  userName,
  activeItemId,
  navItems,
  onNavigate,
}) {
  if (!isOpen) return null;

  const handleNavClick = (item, e) => {
    if (onNavigate) {
      e.preventDefault();
      onNavigate(item);
    }
    onClose();
  };

  return (
    <>
      {/* Overlay backdrop */}
      <div
        className="mobile-sidebar-overlay"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar panel */}
      <aside className="mobile-sidebar">
        <div className="mobile-sidebar-header">
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-sidebar-foreground truncate">
              Refinance Monitor
            </p>
            {userName && (
              <p className="text-xs text-sidebar-foreground/60 truncate">
                {userName}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-sidebar-hover transition-colors"
            aria-label="Close menu"
          >
            <Icons.X className="w-5 h-5" />
          </button>
        </div>

        <div className="sidebar-content">
          {navItems.map((section, sectionIndex) => (
            <div key={sectionIndex} className="mb-4">
              {section.section && (
                <div className="sidebar-section-title">
                  {section.section}
                </div>
              )}
              <nav className="sidebar-nav">
                {section.items.map((item) => {
                  const IconComponent = Icons[item.icon];
                  return (
                    <a
                      key={item.id}
                      href={item.href}
                      target={item.external ? '_blank' : undefined}
                      rel={item.external ? 'noopener noreferrer' : undefined}
                      onClick={(e) => handleNavClick(item, e)}
                      className={cn(
                        'sidebar-nav-item',
                        activeItemId === item.id && 'sidebar-nav-item-active'
                      )}
                    >
                      {IconComponent && (
                        <IconComponent className="sidebar-nav-icon" />
                      )}
                      <span className="sidebar-nav-label">{item.label}</span>
                    </a>
                  );
                })}
              </nav>
            </div>
          ))}
        </div>

        <div className="sidebar-footer">
          <a
            href="/logout"
            className={cn(
              'sidebar-nav-item',
              'text-destructive hover:text-destructive hover:bg-destructive/10'
            )}
          >
            <Icons.Logout className="sidebar-nav-icon" />
            <span className="sidebar-nav-label">Logout</span>
          </a>
        </div>
      </aside>
    </>
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
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Get default nav items from Sidebar if not provided
  const defaultNavItems = [
    {
      section: 'Dashboard',
      items: [
        { id: 'home', label: 'Home', icon: 'Home', href: '/dashboard' },
        { id: 'calculator', label: 'Calculator', icon: 'Calculator', href: '/calculator/', external: true },
        { id: 'manage', label: 'Manage', icon: 'Inbox', href: '/manage' },
        { id: 'history', label: 'History', icon: 'Clock', href: '/history' },
      ],
    },
    {
      section: 'Settings',
      items: [
        { id: 'profile', label: 'Profile', icon: 'User', href: '/profile' },
        { id: 'settings', label: 'Settings', icon: 'Settings', href: '/settings' },
      ],
    },
  ];

  const resolvedNavItems = navItems || defaultNavItems;

  return (
    <DashboardLayoutContext.Provider
      value={{
        isSidebarCollapsed,
        setIsSidebarCollapsed,
        isMobileMenuOpen,
        setIsMobileMenuOpen,
      }}
    >
      <div className={cn('dashboard-layout dark', className)}>
        {/* Desktop sidebar */}
        <Sidebar
          userName={userName}
          activeItemId={activeNavItem}
          navItems={resolvedNavItems}
          defaultCollapsed={defaultCollapsed}
          onNavigate={onNavigate}
        />

        {/* Mobile sidebar overlay */}
        <MobileSidebar
          isOpen={isMobileMenuOpen}
          onClose={() => setIsMobileMenuOpen(false)}
          userName={userName}
          activeItemId={activeNavItem}
          navItems={resolvedNavItems}
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
  MobileSidebar,
};

export default DashboardLayout;
