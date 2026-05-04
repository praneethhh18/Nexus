import { useEffect, useRef, useState } from 'react';

export default function BlurText({
  text = '',
  delay = 110,
  className = '',
  animateBy = 'words',
  tag: Tag = 'p',
  style = {},
}) {
  const elements = animateBy === 'words' ? text.split(' ') : text.split('');
  const [inView, setInView] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); obs.disconnect(); } },
      { threshold: 0.05 }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);

  return (
    <Tag
      ref={ref}
      className={className}
      style={{ display: 'flex', flexWrap: 'wrap', ...style }}
    >
      {elements.map((seg, i) => (
        <span
          key={i}
          className={inView ? 'blur-word blur-word-in' : 'blur-word'}
          style={{ animationDelay: `${i * delay}ms` }}
        >
          {seg}
          {animateBy === 'words' && ' '}
        </span>
      ))}
    </Tag>
  );
}
