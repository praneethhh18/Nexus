import { motion } from 'motion/react';
import { useEffect, useRef, useState, useMemo } from 'react';

const buildKeyframes = (from, steps) => {
  const keys = new Set([...Object.keys(from), ...steps.flatMap(s => Object.keys(s))]);
  const keyframes = {};
  keys.forEach(k => { keyframes[k] = [from[k], ...steps.map(s => s[k])]; });
  return keyframes;
};

export default function BlurText({
  text = '',
  delay = 120,
  className = '',
  animateBy = 'words',
  direction = 'bottom',
  threshold = 0.1,
  rootMargin = '0px',
  stepDuration = 0.38,
  tag: Tag = 'p',
  style = {},
  onAnimationComplete,
}) {
  const elements = animateBy === 'words' ? text.split(' ') : text.split('');
  const [inView, setInView] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); obs.disconnect(); } },
      { threshold, rootMargin }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [threshold, rootMargin]);

  const from = useMemo(() => ({
    filter: 'blur(10px)',
    opacity: 0,
    y: direction === 'top' ? -40 : 40,
  }), [direction]);

  const to = useMemo(() => [
    { filter: 'blur(4px)',  opacity: 0.5, y: direction === 'top' ? 4 : -4 },
    { filter: 'blur(0px)',  opacity: 1,   y: 0 },
  ], [direction]);

  const stepCount    = to.length + 1;
  const totalDur     = stepDuration * (stepCount - 1);
  const times        = Array.from({ length: stepCount }, (_, i) => i / (stepCount - 1));

  return (
    <Tag ref={ref} className={className} style={{ display: 'flex', flexWrap: 'wrap', ...style }}>
      {elements.map((seg, i) => (
        <motion.span
          key={i}
          style={{ display: 'inline-block', willChange: 'transform, filter, opacity' }}
          initial={from}
          animate={inView ? buildKeyframes(from, to) : from}
          transition={{ duration: totalDur, times, delay: (i * delay) / 1000, ease: 'easeOut' }}
          onAnimationComplete={i === elements.length - 1 ? onAnimationComplete : undefined}
        >
          {seg === ' ' ? ' ' : seg}
          {animateBy === 'words' && i < elements.length - 1 && ' '}
        </motion.span>
      ))}
    </Tag>
  );
}
