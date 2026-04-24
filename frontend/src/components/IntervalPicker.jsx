/**
 * Dropdown interval picker — pick from presets or type a custom value in minutes.
 *
 * <IntervalPicker value={15} presets={[5,10,15,30,60,180,...]} onChange={fn} />
 *
 * Matches the shape of `api.agent_schedule.INTERVAL_PRESETS_MIN` but accepts
 * any list so individual pages can offer their own cadence vocabulary.
 */
import { useState, useEffect, useRef } from 'react';
import { Clock, ChevronDown, Check, RotateCcw } from 'lucide-react';


function humanLabel(minutes) {
  if (minutes >= 10080 && minutes % 10080 === 0) {
    const w = minutes / 10080;
    return w === 1 ? 'Weekly' : `Every ${w} weeks`;
  }
  if (minutes >= 1440 && minutes % 1440 === 0) {
    const d = minutes / 1440;
    return d === 1 ? 'Daily' : `Every ${d} days`;
  }
  if (minutes >= 60 && minutes % 60 === 0) {
    const h = minutes / 60;
    return h === 1 ? 'Hourly' : `Every ${h} hr`;
  }
  return `Every ${minutes} min`;
}


export default function IntervalPicker({
  value,
  defaultValue = null,
  presets = [5, 10, 15, 30, 60, 180, 360, 720, 1440, 4320, 10080],
  onChange,
  onReset,
  minMinutes = 5,
  maxMinutes = 10080,
  size = 'sm',
}) {
  const [open, setOpen] = useState(false);
  const [customVal, setCustomVal] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    if (open) {
      window.addEventListener('mousedown', onClick);
      return () => window.removeEventListener('mousedown', onClick);
    }
  }, [open]);

  const isCustom = defaultValue != null && value !== defaultValue;

  const pick = (n) => {
    onChange?.(n);
    setOpen(false);
  };

  const applyCustom = () => {
    const n = parseInt(customVal, 10);
    if (!Number.isFinite(n) || n < minMinutes || n > maxMinutes) return;
    setCustomVal('');
    pick(n);
  };

  return (
    <div ref={ref} style={{ position: 'relative', display: 'inline-block' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="btn-ghost"
        style={{
          fontSize: size === 'sm' ? 11 : 12,
          padding: size === 'sm' ? '4px 10px' : '6px 12px',
          display: 'inline-flex', alignItems: 'center', gap: 6,
          background: isCustom
            ? 'color-mix(in srgb, var(--color-accent) 10%, transparent)'
            : 'var(--color-surface-1)',
          border: `1px solid ${isCustom
            ? 'color-mix(in srgb, var(--color-accent) 35%, transparent)'
            : 'var(--color-border)'}`,
        }}
        title={isCustom ? 'Custom interval — click to change' : 'Click to change schedule'}
      >
        <Clock size={11} color={isCustom ? 'var(--color-accent)' : 'var(--color-text-dim)'} />
        <span>{humanLabel(value)}</span>
        <ChevronDown size={10} color="var(--color-text-dim)" />
      </button>

      {open && (
        <div
          style={{
            position: 'absolute', top: '100%', left: 0, marginTop: 4,
            background: 'var(--color-bg)', border: '1px solid var(--color-surface-2)',
            borderRadius: 'var(--r-md)', padding: 6, minWidth: 200, zIndex: 120,
            boxShadow: '0 12px 32px rgba(0,0,0,0.5)',
          }}
        >
          {presets.map(n => {
            const selected = n === value;
            return (
              <button
                key={n}
                onClick={() => pick(n)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6,
                  padding: '6px 10px', borderRadius: 'var(--r-sm)',
                  background: selected ? 'color-mix(in srgb, var(--color-accent) 12%, transparent)' : 'transparent',
                  border: 'none', cursor: 'pointer', width: '100%', textAlign: 'left',
                  color: 'var(--color-text)', fontSize: 12,
                }}
              >
                {selected ? <Check size={11} color="var(--color-accent)" /> : <span style={{ width: 11 }} />}
                {humanLabel(n)}
                {defaultValue === n && (
                  <span style={{ marginLeft: 'auto', fontSize: 9, color: 'var(--color-text-dim)' }}>default</span>
                )}
              </button>
            );
          })}

          <div style={{
            borderTop: '1px solid var(--color-border)', marginTop: 4, paddingTop: 6,
            display: 'flex', gap: 4, alignItems: 'center',
          }}>
            <input
              type="number"
              placeholder="Custom min"
              value={customVal}
              onChange={(e) => setCustomVal(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') applyCustom(); }}
              className="field-input"
              style={{ fontSize: 11, padding: '4px 6px', flex: 1 }}
              min={minMinutes}
              max={maxMinutes}
            />
            <button onClick={applyCustom} className="btn-ghost" style={{ fontSize: 11 }}>
              Set
            </button>
          </div>

          {onReset && isCustom && (
            <button
              onClick={() => { setOpen(false); onReset(); }}
              className="btn-ghost"
              style={{
                fontSize: 11, marginTop: 4, padding: '4px 6px', width: '100%',
                display: 'inline-flex', alignItems: 'center', gap: 4, color: 'var(--color-text-dim)',
              }}
            >
              <RotateCcw size={10} /> Reset to default ({humanLabel(defaultValue)})
            </button>
          )}
        </div>
      )}
    </div>
  );
}
