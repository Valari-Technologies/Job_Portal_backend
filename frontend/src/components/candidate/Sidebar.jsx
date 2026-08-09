import React, { useEffect, useRef, useState } from 'react';
import { Home, Briefcase, FileText, User, Settings } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import logoJobz from '../../assets/logo-jobz.png';

const SIDEBAR_BG = '#84A43C';
const CORNER_RADIUS = 40; // rounded top/bottom cap of the bar
const PINCH_RATIO = 0.29; // how far the right edge dips inward at the active icon (0-1)
const DIP_HALF_HEIGHT = 30; // px, fixed vertical reach of the dip above/below the active icon - kept small and constant regardless of bar height

// Builds the sidebar's silhouette: a perfectly STRAIGHT edge everywhere,
// except a single localized concave dip around `activeY` (the currently
// active nav item's vertical center) - a rounded bulge above the dip, a
// pinch right at the icon, and a rounded bulge below it flowing back to the
// straight edge. Only one dip exists at a time; it moves as the active route
// changes. Uses real measured pixel width/height so the corner radius and
// dip depth stay proportionally correct at any viewport size.
function buildWavePath(width, height, activeY, bandHalf) {
  if (!width || !height) return '';

  const r = Math.min(CORNER_RADIUS, height / 4, width);

  if (activeY == null) {
    return `M0,${r} Q0,0 ${r},0 L${width - r},0 Q${width},0 ${width},${r} L${width},${height - r} Q${width},${height} ${width - r},${height} L${r},${height} Q0,${height} 0,${height - r} Z`;
  }

  const pinchX = width * (1 - PINCH_RATIO);
  const topY = Math.max(r, activeY - bandHalf);
  const botY = Math.min(height - r, activeY + bandHalf);
  const midTop = (topY + activeY) / 2;
  const midBot = (activeY + botY) / 2;

  let d = `M0,${r} Q0,0 ${r},0 L${width - r},0 Q${width},0 ${width},${r} `;
  d += `L${width},${topY} `;
  d += `C${width},${midTop} ${pinchX},${midTop} ${pinchX},${activeY} `;
  d += `C${pinchX},${midBot} ${width},${midBot} ${width},${botY} `;
  d += `L${width},${height - r} Q${width},${height} ${width - r},${height} L${r},${height} Q0,${height} 0,${height - r} Z`;

  return d;
}

export default function Sidebar() {
  const location = useLocation();
  const asideRef = useRef(null);
  const itemRefs = useRef({});
  const [size, setSize] = useState({ width: 0, height: 0 });
  const [activeY, setActiveY] = useState(null);

  const isRouteActive = (path, end = false) => {
    const current = location.pathname.endsWith('/') && location.pathname.length > 1
      ? location.pathname.slice(0, -1)
      : location.pathname;
    const target = path.endsWith('/') && path.length > 1
      ? path.slice(0, -1)
      : path;
    if (end) {
      return current === target;
    }
    return current.startsWith(target);
  };

  const navItems = [
    { to: '/dashboard', icon: Home, end: true, label: 'Dashboard' },
    { to: '/dashboard/jobs', icon: Briefcase, end: false, label: 'Find Jobs' },
    { to: '/dashboard/applications', icon: FileText, end: false, label: 'Applications' },
    { to: '/dashboard/profile', icon: User, end: false, label: 'Profile' },
    { to: '/dashboard/settings', icon: Settings, end: false, label: 'Settings' }
  ];

  const activeTo = navItems.find((item) => isRouteActive(item.to, item.end))?.to;

  // Measure the sidebar's real pixel size so the corner radius and dip
  // amplitude stay proportional at any viewport width/height.
  useEffect(() => {
    const el = asideRef.current;
    if (!el) return undefined;

    const updateSize = () => {
      const rect = el.getBoundingClientRect();
      setSize({ width: rect.width, height: rect.height });
    };

    updateSize();
    const observer = new ResizeObserver(updateSize);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Measure the active item's real vertical center each time the route (or
  // layout) changes, so the dip always tracks the item that matches the
  // top navigation's current page - moving smoothly to it via a CSS
  // transition on the SVG path itself.
  useEffect(() => {
    const measure = () => {
      const aside = asideRef.current;
      const activeEl = activeTo && itemRefs.current[activeTo];
      if (!aside || !activeEl) return;
      const asideRect = aside.getBoundingClientRect();
      const itemRect = activeEl.getBoundingClientRect();
      setActiveY(itemRect.top - asideRect.top + itemRect.height / 2);
    };

    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, [activeTo, size.height]);

  const bandHalf = size.height ? DIP_HALF_HEIGHT : 0;
  const wavePath = buildWavePath(size.width, size.height, activeY, bandHalf);
  const iconOffset = (size.width * PINCH_RATIO) / 2;

  return (
    <div className="w-16 md:w-18 min-h-[96vh] flex flex-col items-center select-none shrink-0 relative z-25">

      <img src={logoJobz} alt="Branding Logo" className="w-12 h-12 md:w-14 md:h-14 object-contain mt-3.5 mb-4 cursor-pointer hover:opacity-90 transition-opacity shrink-0" />

      {/* Main Sidebar Body - straight edges; a single dip nests around whichever icon is active */}
      <aside ref={asideRef} className="w-full flex-grow relative flex flex-col items-center justify-start pt-16">
        {wavePath && (
          <svg
            className="absolute inset-0 pointer-events-none"
            width={size.width}
            height={size.height}
            viewBox={`0 0 ${size.width} ${size.height}`}
            aria-hidden="true"
          >
            <path
              d={wavePath}
              fill={SIDEBAR_BG}
              style={{ transition: 'd 0.4s cubic-bezier(0.4, 0, 0.2, 1)' }}
            />
          </svg>
        )}

        {/* Navigation Menu - clustered close together, centered in the bar */}
        <nav className="relative z-20 flex flex-col items-center gap-8 md:gap-9">
          {navItems.map((item) => {
            const active = isRouteActive(item.to, item.end);
            const Icon = item.icon;

            return (
              <NavLink
                key={item.to}
                ref={(el) => (itemRefs.current[item.to] = el)}
                to={item.to}
                end={item.end}
                className={`w-10 h-10 md:w-11 md:h-11 flex items-center justify-center transition-all duration-[400ms] cursor-pointer ${
                  active ? 'text-white' : 'text-white/60 hover:text-white'
                }`}
                style={{ transform: active ? `translateX(-${iconOffset}px) scale(1.1)` : undefined }}
                aria-label={item.label}
              >
                <Icon className="w-5 h-5 md:w-6 md:h-6" />
              </NavLink>
            );
          })}
        </nav>
      </aside>
    </div>
  );
}
