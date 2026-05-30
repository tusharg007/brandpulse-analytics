/**
 * Navbar — Professional top navigation bar.
 */
import { NavLink } from 'react-router-dom';
import { HiChartBar, HiCube, HiChatBubbleLeftRight } from 'react-icons/hi2';
import LiveIndicator from './LiveIndicator';

const navLinks = [
  { to: '/', label: 'Dashboard', icon: HiChartBar },
  { to: '/brands', label: 'Brands', icon: HiCube },
  { to: '/chat', label: 'Intelligence Feed', icon: HiChatBubbleLeftRight },
];

export default function Navbar({ isConnected }) {
  return (
    <nav style={{
      height: 56, background: 'var(--bg-surface)',
      borderBottom: '1px solid var(--bg-border)',
      display: 'flex', alignItems: 'center',
      padding: '0 32px', position: 'sticky', top: 0, zIndex: 50,
    }}>
      {/* Left — Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{
          width: 28, height: 28, borderRadius: 6,
          background: 'var(--accent-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, color: '#fff',
        }}>BP</div>
        <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
          BrandPulse
        </span>
        <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 2 }}>Analytics</span>
      </div>

      {/* Center — Nav links */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, margin: '0 auto' }}>
        {navLinks.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '6px 14px', borderRadius: 6,
              fontSize: 13, fontWeight: 500,
              color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
              background: isActive ? 'var(--bg-elevated)' : 'transparent',
              textDecoration: 'none',
              borderBottom: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
              transition: 'color 200ms, background 200ms',
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </div>

      {/* Right — Live indicator */}
      <LiveIndicator connected={isConnected} />
    </nav>
  );
}
