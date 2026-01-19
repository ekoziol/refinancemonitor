import React from 'react';
import { cn } from '../../lib/utils';
import { Icons } from './Sidebar';

/**
 * TopBar - Dashboard top navigation bar with mobile menu toggle.
 *
 * Provides:
 * - Mobile hamburger menu button (shows on small screens)
 * - Page title and subtitle
 * - Action buttons area (notifications, user menu, etc.)
 *
 * @param {Object} props
 * @param {string} props.title - Page title
 * @param {string} props.subtitle - Optional page subtitle
 * @param {Function} props.onMenuClick - Callback when mobile menu is clicked
 * @param {React.ReactNode} props.children - Additional action items
 * @param {string} props.className - Additional CSS classes
 */
function TopBar({
  title,
  subtitle,
  onMenuClick,
  children,
  className,
}) {
  return (
    <header className={cn('topbar', className)}>
      {/* Mobile menu button */}
      <button
        type="button"
        onClick={onMenuClick}
        className="topbar-menu-btn md:hidden"
        aria-label="Open navigation menu"
      >
        <Icons.Menu className="w-6 h-6" />
      </button>

      {/* Title section */}
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

      {/* Actions area */}
      {children && (
        <div className="flex items-center gap-2 md:gap-4">
          {children}
        </div>
      )}
    </header>
  );
}

/**
 * TopBarAction - Styled button for TopBar actions.
 */
function TopBarAction({
  icon: IconComponent,
  label,
  onClick,
  badge,
  className,
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn('topbar-action', className)}
      aria-label={label}
      title={label}
    >
      {IconComponent && <IconComponent className="w-5 h-5" />}
      {badge && (
        <span className="topbar-action-badge">{badge}</span>
      )}
    </button>
  );
}

/**
 * TopBarUserMenu - User avatar and dropdown trigger.
 */
function TopBarUserMenu({
  userName,
  userEmail,
  avatarUrl,
  onClick,
  className,
}) {
  const initials = userName
    ? userName
        .split(' ')
        .map((n) => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2)
    : '?';

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn('topbar-user', className)}
      aria-label="User menu"
    >
      {avatarUrl ? (
        <img
          src={avatarUrl}
          alt={userName}
          className="w-8 h-8 rounded-full"
        />
      ) : (
        <div className="topbar-user-avatar">
          {initials}
        </div>
      )}
      <span className="hidden md:block text-sm font-medium truncate max-w-[120px]">
        {userName}
      </span>
      <Icons.ChevronDown className="hidden md:block w-4 h-4 text-muted-foreground" />
    </button>
  );
}

export { TopBar, TopBarAction, TopBarUserMenu };
export default TopBar;
