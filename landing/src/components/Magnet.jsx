import { useState, useEffect, useRef } from 'react';

export default function Magnet({
  children,
  padding = 80,
  disabled = false,
  magnetStrength = 3,
  activeTransition   = 'transform 0.3s ease-out',
  inactiveTransition = 'transform 0.5s ease-in-out',
  style = {},
}) {
  const [isActive, setIsActive] = useState(false);
  const [pos, setPos]           = useState({ x: 0, y: 0 });
  const ref = useRef(null);

  useEffect(() => {
    if (disabled) { setPos({ x: 0, y: 0 }); return; }

    const onMove = e => {
      if (!ref.current) return;
      const { left, top, width, height } = ref.current.getBoundingClientRect();
      const cx = left + width  / 2;
      const cy = top  + height / 2;
      if (Math.abs(cx - e.clientX) < width / 2 + padding &&
          Math.abs(cy - e.clientY) < height / 2 + padding) {
        setIsActive(true);
        setPos({ x: (e.clientX - cx) / magnetStrength, y: (e.clientY - cy) / magnetStrength });
      } else {
        setIsActive(false);
        setPos({ x: 0, y: 0 });
      }
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, [padding, disabled, magnetStrength]);

  return (
    <div ref={ref} style={{ display: 'inline-block', ...style }}>
      <div style={{
        transform: `translate3d(${pos.x}px,${pos.y}px,0)`,
        transition: isActive ? activeTransition : inactiveTransition,
        willChange: 'transform',
      }}>
        {children}
      </div>
    </div>
  );
}
