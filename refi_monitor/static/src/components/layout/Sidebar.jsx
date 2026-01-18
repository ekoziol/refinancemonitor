import React, { useState } from 'react';
import { cn } from '../../lib/utils';

/**
 * Icon components using inline SVGs for sidebar navigation.
 * These match the existing icons in main_layout.jinja2.
 */
const Icons = {
  Home: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  ),
  Calculator: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
    </svg>
  ),
  Inbox: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
  ),
  Clock: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  User: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
    </svg>
  ),
  Settings: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  ),
  Logout: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
    </svg>
  ),
  ChevronLeft: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
    </svg>
  ),
  ChevronRight: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
    </svg>
  ),
  Chart: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  Bell: ({ className }) => (
    <svg className={className} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
    </svg>
  ),
};

/**
 * Navigation items configuration.
 * Each item has an id, label, icon, and href.
 */
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

/**
 * SidebarNavItem - Individual navigation item component.
 */
function SidebarNavItem({ item, isActive, isCollapsed, onClick }) {
  const IconComponent = Icons[item.icon];

  return (
    <a
      href={item.href}
      target={item.external ? '_blank' : undefined}
      rel={item.external ? 'noopener noreferrer' : undefined}
      onClick={onClick}
      className={cn(
        'sidebar-nav-item',
        isActive && 'sidebar-nav-item-active'
      )}
      title={isCollapsed ? item.label : undefined}
    >
      {IconComponent && (
        <IconComponent className="sidebar-nav-icon" />
      )}
      {!isCollapsed && (
        <span className="sidebar-nav-label">{item.label}</span>
      )}
    </a>
  );
}

/**
 * Sidebar - Glass-morphism sidebar navigation component.
 *
 * @param {Object} props
 * @param {string} props.userName - Current user's name
 * @param {string} props.activeItemId - ID of the currently active nav item
 * @param {Array} props.navItems - Navigation items configuration
 * @param {boolean} props.defaultCollapsed - Whether sidebar starts collapsed
 * @param {Function} props.onNavigate - Callback when navigation item is clicked
 * @param {string} props.className - Additional CSS classes
 */
function Sidebar({
  userName = '',
  activeItemId = 'home',
  navItems = defaultNavItems,
  defaultCollapsed = false,
  onNavigate,
  className,
}) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  const handleToggle = () => {
    setIsCollapsed(!isCollapsed);
  };

  const handleNavClick = (item, e) => {
    if (onNavigate) {
      e.preventDefault();
      onNavigate(item);
    }
  };

  return (
    <aside
      className={cn(
        'sidebar',
        isCollapsed && 'sidebar-collapsed',
        className
      )}
    >
      {/* Sidebar Header */}
      <div className="sidebar-header">
        {!isCollapsed && (
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
        )}
        <button
          onClick={handleToggle}
          className="p-1.5 rounded-md hover:bg-sidebar-hover transition-colors"
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? (
            <Icons.ChevronRight className="w-4 h-4" />
          ) : (
            <Icons.ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Sidebar Content */}
      <div className="sidebar-content">
        {navItems.map((section, sectionIndex) => (
          <div key={sectionIndex} className="mb-4">
            {!isCollapsed && section.section && (
              <div className="sidebar-section-title">
                {section.section}
              </div>
            )}
            <nav className="sidebar-nav">
              {section.items.map((item) => (
                <SidebarNavItem
                  key={item.id}
                  item={item}
                  isActive={activeItemId === item.id}
                  isCollapsed={isCollapsed}
                  onClick={(e) => handleNavClick(item, e)}
                />
              ))}
            </nav>
          </div>
        ))}
      </div>

      {/* Sidebar Footer */}
      <div className="sidebar-footer">
        <a
          href="/logout"
          className={cn(
            'sidebar-nav-item',
            'text-destructive hover:text-destructive hover:bg-destructive/10'
          )}
          title={isCollapsed ? 'Logout' : undefined}
        >
          <Icons.Logout className="sidebar-nav-icon" />
          {!isCollapsed && (
            <span className="sidebar-nav-label">Logout</span>
          )}
        </a>
      </div>
    </aside>
  );
}

export { Sidebar, Icons };
export default Sidebar;
